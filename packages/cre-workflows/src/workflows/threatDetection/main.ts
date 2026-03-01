/**
 * AEGIS Threat Detection Workflow
 *
 * Primary CRE workflow that orchestrates the full detection cycle:
 *  1. Cron trigger (every 60s via Chainlink Automation) or HTTP trigger
 *  2. Read on-chain data (MockProtocol TVL, Chainlink ETH/USD price)
 *  3. Call Python agent API for AI threat detection (3 sentinels + consensus)
 *  4. If CRITICAL → trigger CircuitBreaker via CRE signed report
 *  5. Submit ThreatReport on-chain with sentinel votes
 *
 * Chainlink services demonstrated:
 *  - CRE (this workflow)
 *  - Data Feeds (Chainlink ETH/USD read)
 *  - Automation (cron trigger)
 */

import {
  cre,
  type Runtime,
  type HTTPSendRequester,
  Runner,
  getNetwork,
  encodeCallMsg,
  bytesToHex,
  hexToBase64,
  TxStatus,
  ok,
  consensusIdenticalAggregation,
} from "@chainlink/cre-sdk";
import {
  type Address,
  encodeFunctionData,
  decodeFunctionResult,
  encodeAbiParameters,
  parseAbiParameters,
  keccak256,
  toHex,
  zeroAddress,
} from "viem";

import {
  circuitBreakerAbi,
  threatReportAbi,
  mockProtocolAbi,
  chainlinkAggregatorAbi,
} from "../../types/abis";
import {
  configSchema,
  type Config,
  type DetectionResponse,
  THREAT_LEVEL_UINT8,
} from "../../types";

// ============ Cron Trigger Callback ============

const onCronTrigger = (runtime: Runtime<Config>): string => {
  runtime.log("AEGIS: Cron-triggered detection cycle starting...");
  return runDetectionCycle(runtime);
};

// ============ Core Detection Logic ============

function runDetectionCycle(runtime: Runtime<Config>): string {
  const evm = runtime.config.evms[0];
  const network = getNetwork({
    chainFamily: "evm",
    chainSelectorName: evm.chainSelectorName,
    isTestnet: true,
  });
  if (!network) throw new Error(`Network not found: ${evm.chainSelectorName}`);

  const evmClient = new cre.capabilities.EVMClient(
    network.chainSelector.selector
  );

  // ---- Step 1: Read on-chain TVL from MockProtocol ----
  runtime.log("Step 1: Reading on-chain TVL...");
  const tvlCallData = encodeFunctionData({
    abi: mockProtocolAbi,
    functionName: "getTVL",
  });
  const tvlResult = evmClient
    .callContract(runtime, {
      call: encodeCallMsg({
        from: zeroAddress,
        to: evm.mockProtocolAddress as Address,
        data: tvlCallData,
      }),
    })
    .result();
  const tvl = decodeFunctionResult({
    abi: mockProtocolAbi,
    functionName: "getTVL",
    data: bytesToHex(tvlResult.data) as `0x${string}`,
  }) as bigint;
  runtime.log(`  TVL: ${tvl.toString()} wei`);

  // ---- Step 2: Read Chainlink ETH/USD price (Data Feeds) ----
  runtime.log("Step 2: Reading Chainlink ETH/USD...");
  const priceCallData = encodeFunctionData({
    abi: chainlinkAggregatorAbi,
    functionName: "latestRoundData",
  });
  const priceResult = evmClient
    .callContract(runtime, {
      call: encodeCallMsg({
        from: zeroAddress,
        to: evm.chainlinkFeeds.ethUsd as Address,
        data: priceCallData,
      }),
    })
    .result();
  const [, answer, , updatedAt] = decodeFunctionResult({
    abi: chainlinkAggregatorAbi,
    functionName: "latestRoundData",
    data: bytesToHex(priceResult.data) as `0x${string}`,
  }) as [bigint, bigint, bigint, bigint, bigint];
  const ethPrice = Number(answer) / 1e8;
  runtime.log(`  ETH/USD: $${ethPrice.toFixed(2)}`);

  // ---- Step 3: Call Python agent API for threat detection ----
  runtime.log("Step 3: Calling AI agent detection API...");
  const httpClient = new cre.capabilities.HTTPClient();

  const fetchDetection = (
    sendRequester: HTTPSendRequester,
    config: Config
  ): DetectionResponse => {
    const bodyBytes = new TextEncoder().encode(
      JSON.stringify({
        protocol_address: evm.mockProtocolAddress,
        protocol_name: "MockProtocol",
      })
    );
    const body = Buffer.from(bodyBytes).toString("base64");

    const resp = sendRequester
      .sendRequest({
        url: `${config.agentApiUrl}/api/v1/detect`,
        method: "POST",
        body,
        headers: { "Content-Type": "application/json" },
      })
      .result();

    if (!ok(resp)) {
      throw new Error(`Agent API returned ${resp.statusCode}`);
    }

    const bodyText = new TextDecoder().decode(resp.body);
    return JSON.parse(bodyText) as DetectionResponse;
  };

  const detection = httpClient
    .sendRequest(
      runtime,
      fetchDetection,
      consensusIdenticalAggregation<DetectionResponse>()
    )(runtime.config)
    .result();

  const { consensus } = detection;
  runtime.log(
    `  Consensus: ${consensus.final_threat_level} (${consensus.agreement_ratio.toFixed(2)}) — reached: ${consensus.consensus_reached}`
  );

  // ---- Step 4: If CRITICAL → trigger CircuitBreaker ----
  if (
    consensus.consensus_reached &&
    consensus.action_recommended === "CIRCUIT_BREAKER"
  ) {
    runtime.log("Step 4: CRITICAL threat — triggering CircuitBreaker...");

    const threatId = keccak256(
      toHex(`aegis-${Date.now()}-${consensus.final_threat_level}`)
    );
    const threatLevelUint8 =
      THREAT_LEVEL_UINT8[consensus.final_threat_level] ?? 0;
    const reason = `AEGIS consensus: ${consensus.final_threat_level} (${consensus.agreement_ratio.toFixed(2)} agreement). ${detection.assessments.map((a) => a.details).join("; ")}`;

    // Encode report payload for CRE signed report
    const reportData = encodeAbiParameters(
      parseAbiParameters(
        "address protocol, bytes32 threatId, uint8 threatLevel, string reason"
      ),
      [
        evm.mockProtocolAddress as Address,
        threatId as `0x${string}`,
        threatLevelUint8,
        reason,
      ]
    );

    const reportResponse = runtime
      .report({
        encodedPayload: hexToBase64(reportData),
        encoderName: "evm",
        signingAlgo: "ecdsa",
        hashingAlgo: "keccak256",
      })
      .result();

    const writeResult = evmClient
      .writeReport(runtime, {
        receiver: evm.circuitBreakerAddress as Address,
        report: reportResponse,
        gasConfig: { gasLimit: evm.gasLimit },
      })
      .result();

    if (writeResult.txStatus === TxStatus.SUCCESS) {
      const txHash = bytesToHex(
        writeResult.txHash ?? new Uint8Array(32)
      );
      runtime.log(`  CircuitBreaker triggered! TX: ${txHash}`);
    } else {
      runtime.log(
        `  CircuitBreaker TX failed: ${writeResult.txStatus}`
      );
    }
  } else if (consensus.consensus_reached) {
    runtime.log(
      `Step 4: Threat level ${consensus.final_threat_level} — alert only, no circuit breaker.`
    );
  } else {
    runtime.log("Step 4: No consensus reached or no threat detected.");
  }

  // ---- Step 5: Submit ThreatReport on-chain ----
  runtime.log("Step 5: Submitting ThreatReport on-chain...");
  const threatLevelUint8 =
    THREAT_LEVEL_UINT8[consensus.final_threat_level] ?? 0;
  const consensusHash = keccak256(
    toHex(JSON.stringify(consensus))
  );
  const actionTaken =
    consensus.action_recommended === "CIRCUIT_BREAKER" &&
    consensus.consensus_reached;

  // Encode the submitReport call
  const votes = consensus.votes.map((v, i) => ({
    sentinelId: BigInt(i),
    threatLevel: THREAT_LEVEL_UINT8[v.threat_level] ?? 0,
    confidence: BigInt(Math.round(v.confidence * 100)),
    signature: "0x" as `0x${string}`,
  }));

  const submitCallData = encodeFunctionData({
    abi: threatReportAbi,
    functionName: "submitReport",
    args: [
      evm.mockProtocolAddress as Address,
      threatLevelUint8,
      consensusHash as `0x${string}`,
      "", // ipfsHash — empty for now
      actionTaken,
      votes,
    ],
  });

  const submitReportData = encodeAbiParameters(
    parseAbiParameters("address to, bytes data"),
    [evm.threatReportAddress as Address, submitCallData]
  );

  const reportResponse2 = runtime
    .report({
      encodedPayload: hexToBase64(submitReportData),
      encoderName: "evm",
      signingAlgo: "ecdsa",
      hashingAlgo: "keccak256",
    })
    .result();

  const writeResult2 = evmClient
    .writeReport(runtime, {
      receiver: evm.threatReportAddress as Address,
      report: reportResponse2,
      gasConfig: { gasLimit: evm.gasLimit },
    })
    .result();

  if (writeResult2.txStatus === TxStatus.SUCCESS) {
    const txHash = bytesToHex(
      writeResult2.txHash ?? new Uint8Array(32)
    );
    runtime.log(`  ThreatReport submitted! TX: ${txHash}`);
  } else {
    runtime.log(`  ThreatReport TX failed: ${writeResult2.txStatus}`);
  }

  return JSON.stringify({
    threatLevel: consensus.final_threat_level,
    consensusReached: consensus.consensus_reached,
    actionTaken,
    tvl: tvl.toString(),
    ethPrice: ethPrice.toFixed(2),
  });
}

// ============ Workflow Initialization ============

const initWorkflow = (config: Config) => {
  const cronCap = new cre.capabilities.CronCapability();

  return [
    // Cron trigger — runs every minute (Chainlink Automation)
    cre.handler(
      cronCap.trigger({ schedule: config.schedule }),
      onCronTrigger
    ),
  ];
};

// ============ Entry Point ============

export async function main() {
  const runner = await Runner.newRunner<Config>({ configSchema });
  await runner.run(initWorkflow);
}

main();

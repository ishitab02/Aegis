/**
 * AEGIS Forensic Analysis Workflow
 *
 * Triggered when CircuitBreaker fires (EVM log trigger on CircuitBreakerTriggered).
 * Calls ChainSherlock for deep forensic analysis and stores report on-chain.
 *
 * Chainlink services: CRE + Log Trigger (Automation)
 */

import {
  cre,
  type Runtime,
  type HTTPSendRequester,
  type EVMLog,
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
  encodeAbiParameters,
  parseAbiParameters,
  decodeEventLog,
  keccak256,
  toHex,
} from "viem";

import { circuitBreakerAbi, threatReportAbi } from "../../types/abis";
import { configSchema, type Config, THREAT_LEVEL_UINT8 } from "../../types";

// ============ Forensic Report Response ============

type ForensicReportResponse = {
  report_id: string;
  tx_hash: string;
  protocol: string;
  attack_classification: {
    primary_type: string;
    confidence: number;
    description: string;
  };
  timestamp: number;
};

// ============ Log Trigger Callback ============

const onCircuitBreakerTriggered = (
  runtime: Runtime<Config>,
  log: EVMLog
): string => {
  runtime.log("AEGIS: CircuitBreakerTriggered event detected!");

  const evm = runtime.config.evms[0];

  // Decode the event log
  const topics = log.topics.map((t) => bytesToHex(t)) as [
    `0x${string}`,
    ...`0x${string}`[],
  ];
  const data = bytesToHex(log.data);

  const decoded = decodeEventLog({
    abi: circuitBreakerAbi,
    eventName: "CircuitBreakerTriggered",
    data: data as `0x${string}`,
    topics,
  });

  const protocol = decoded.args.protocol as Address;
  const threatId = decoded.args.threatId as `0x${string}`;
  runtime.log(`  Protocol: ${protocol}`);
  runtime.log(`  ThreatId: ${threatId}`);

  // ---- Call ChainSherlock forensics API ----
  runtime.log("Calling ChainSherlock forensic analysis...");
  const httpClient = new cre.capabilities.HTTPClient();

  const fetchForensics = (
    sendRequester: HTTPSendRequester,
    config: Config
  ): ForensicReportResponse => {
    const bodyBytes = new TextEncoder().encode(
      JSON.stringify({
        tx_hash: threatId, // Use threatId as a reference; real impl would extract tx hash
        protocol: protocol,
        description: `Automated forensic analysis triggered by CircuitBreaker event`,
      })
    );
    const body = Buffer.from(bodyBytes).toString("base64");

    const resp = sendRequester
      .sendRequest({
        url: `${config.agentApiUrl}/api/v1/forensics`,
        method: "POST",
        body,
        headers: { "Content-Type": "application/json" },
      })
      .result();

    if (!ok(resp)) {
      throw new Error(`Forensics API returned ${resp.statusCode}`);
    }

    const bodyText = new TextDecoder().decode(resp.body);
    return JSON.parse(bodyText) as ForensicReportResponse;
  };

  const report = httpClient
    .sendRequest(
      runtime,
      fetchForensics,
      consensusIdenticalAggregation<ForensicReportResponse>()
    )(runtime.config)
    .result();

  runtime.log(
    `  Attack type: ${report.attack_classification.primary_type} (${report.attack_classification.confidence})`
  );
  runtime.log(`  Report ID: ${report.report_id}`);

  // ---- Store forensic report hash on-chain via ThreatReport ----
  runtime.log("Submitting forensic report reference on-chain...");
  const network = getNetwork({
    chainFamily: "evm",
    chainSelectorName: evm.chainSelectorName,
    isTestnet: true,
  });
  if (!network) throw new Error(`Network not found: ${evm.chainSelectorName}`);

  const evmClient = new cre.capabilities.EVMClient(
    network.chainSelector.selector
  );

  const reportHash = keccak256(toHex(JSON.stringify(report)));

  const submitCallData = encodeFunctionData({
    abi: threatReportAbi,
    functionName: "submitReport",
    args: [
      protocol,
      THREAT_LEVEL_UINT8["CRITICAL"],
      reportHash as `0x${string}`,
      report.report_id, // Store report_id as IPFS hash placeholder
      true, // actionTaken = true (circuit breaker was triggered)
      [], // No individual votes for forensic reports
    ],
  });

  const reportData = encodeAbiParameters(
    parseAbiParameters("address to, bytes data"),
    [evm.threatReportAddress as Address, submitCallData]
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
      receiver: evm.threatReportAddress as Address,
      report: reportResponse,
      gasConfig: { gasLimit: evm.gasLimit },
    })
    .result();

  if (writeResult.txStatus === TxStatus.SUCCESS) {
    const txHash = bytesToHex(writeResult.txHash ?? new Uint8Array(32));
    runtime.log(`  Forensic report submitted on-chain! TX: ${txHash}`);
  } else {
    runtime.log(`  Report TX failed: ${writeResult.txStatus}`);
  }

  return JSON.stringify({
    reportId: report.report_id,
    attackType: report.attack_classification.primary_type,
    confidence: report.attack_classification.confidence,
  });
};

// ============ Workflow Initialization ============

const initWorkflow = (config: Config) => {
  const evm = config.evms[0];
  const network = getNetwork({
    chainFamily: "evm",
    chainSelectorName: evm.chainSelectorName,
    isTestnet: true,
  });
  if (!network) throw new Error(`Network not found: ${evm.chainSelectorName}`);

  const evmClient = new cre.capabilities.EVMClient(
    network.chainSelector.selector
  );

  // Listen for CircuitBreakerTriggered events
  const eventSignature =
    "CircuitBreakerTriggered(address,bytes32,uint8,string)";
  const eventHash = keccak256(toHex(eventSignature));

  return [
    cre.handler(
      evmClient.logTrigger({
        addresses: [evm.circuitBreakerAddress],
        topics: [{ values: [eventHash] }],
        confidence: "CONFIDENCE_LEVEL_FINALIZED",
      }),
      onCircuitBreakerTriggered
    ),
  ];
};

// ============ Entry Point ============

export async function main() {
  const runner = await Runner.newRunner<Config>({ configSchema });
  await runner.run(initWorkflow);
}

main();

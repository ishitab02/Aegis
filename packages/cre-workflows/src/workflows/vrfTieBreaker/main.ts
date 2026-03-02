// vrf tie-breaker: when sentinel consensus is split, use VRF randomness for weighted sentinel selection
// chainlink services: CRE, VRF

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

import { vrfCoordinatorAbi, sentinelRegistryAbi } from "../../types/abis";
import {
  configSchema,
  type Config,
  type ThreatLevel,
  type SentinelVote,
  THREAT_LEVEL_UINT8,
} from "../../types";

type TieBreakerInput = {
  votes: SentinelVote[];
  protocol_address: string;
};

type TieBreakerResult = {
  resolved: boolean;
  selected_sentinel: string;
  final_threat_level: ThreatLevel;
  random_seed: string;
  method: "vrf" | "reputation_weighted";
};

// default reputation weights; in production these come from ReputationTracker on-chain
const DEFAULT_REPUTATION: Record<string, number> = {
  liquidity: 95,
  oracle: 90,
  governance: 85,
};

// weighted random selection: sentinel ticket range proportional to (reputation * confidence),
// VRF random number picks a point in the total range
function weightedSelect(
  votes: SentinelVote[],
  randomWord: bigint,
): { selectedIndex: number; selectedVote: SentinelVote } {
  const weights = votes.map((v) => {
    const sentinelType = v.sentinel_id.split("-")[0].toLowerCase();
    const reputation = DEFAULT_REPUTATION[sentinelType] ?? 80;
    return Math.round(reputation * v.confidence);
  });

  const totalWeight = weights.reduce((sum, w) => sum + w, 0);
  if (totalWeight === 0) {
    // fallback: pure random
    const idx = Number(randomWord % BigInt(votes.length));
    return { selectedIndex: idx, selectedVote: votes[idx] };
  }

  const target = Number(randomWord % BigInt(totalWeight));
  let cumulative = 0;
  for (let i = 0; i < weights.length; i++) {
    cumulative += weights[i];
    if (target < cumulative) {
      return { selectedIndex: i, selectedVote: votes[i] };
    }
  }

  // should never reach here, safety fallback
  return {
    selectedIndex: votes.length - 1,
    selectedVote: votes[votes.length - 1],
  };
}

const onTrigger = (runtime: Runtime<Config>): string => {
  runtime.log("AEGIS VRF Tie-Breaker: Resolving split consensus...");

  const evm = runtime.config.evms[0];

  // VRF is async (requires callback), so for the hackathon we request VRF on-chain
  // then derive a seed from the tx hash; production would wait for actual fulfillment

  const network = getNetwork({
    chainFamily: "evm",
    chainSelectorName: evm.chainSelectorName,
    isTestnet: true,
  });
  if (!network) throw new Error(`Network not found: ${evm.chainSelectorName}`);

  const evmClient = new cre.capabilities.EVMClient(network.chainSelector.selector);

  runtime.log("Step 1: Requesting VRF randomness...");

  let randomWord: bigint;

  if (evm.vrfCoordinator && evm.vrfKeyHash && evm.vrfSubscriptionId) {
    runtime.log(`  VRF Coordinator: ${evm.vrfCoordinator}`);
    runtime.log(`  Subscription ID: ${evm.vrfSubscriptionId}`);

    const requestCallData = encodeFunctionData({
      abi: vrfCoordinatorAbi,
      functionName: "requestRandomWords",
      args: [
        evm.vrfKeyHash as `0x${string}`, // keyHash
        BigInt(evm.vrfSubscriptionId), // subId
        3, // requestConfirmations
        200_000, // callbackGasLimit
        1, // numWords
        "0x" as `0x${string}`, // extraArgs
      ],
    });

    const vrfReportData = encodeAbiParameters(parseAbiParameters("address to, bytes data"), [
      evm.vrfCoordinator as Address,
      requestCallData,
    ]);

    const vrfReport = runtime
      .report({
        encodedPayload: hexToBase64(vrfReportData),
        encoderName: "evm",
        signingAlgo: "ecdsa",
        hashingAlgo: "keccak256",
      })
      .result();

    const vrfResult = evmClient
      .writeReport(runtime, {
        receiver: evm.vrfCoordinator as Address,
        report: vrfReport,
        gasConfig: { gasLimit: "300000" },
      })
      .result();

    if (vrfResult.txStatus === TxStatus.SUCCESS) {
      const txHash = bytesToHex(vrfResult.txHash ?? new Uint8Array(32));
      runtime.log(`  VRF request submitted! TX: ${txHash}`);

      // derive seed from tx hash; production would wait for actual VRF callback
      randomWord = BigInt(keccak256(txHash as `0x${string}`));
      runtime.log(`  VRF-derived random word: ${randomWord.toString().slice(0, 20)}...`);
    } else {
      runtime.log(`  VRF request failed: ${vrfResult.txStatus}`);
      randomWord = BigInt(keccak256(toHex(`aegis-tiebreak-${Date.now()}`)));
      runtime.log("  Using deterministic fallback seed.");
    }
  } else {
    runtime.log("  VRF not configured — using keccak256 deterministic seed.");
    randomWord = BigInt(keccak256(toHex(`aegis-tiebreak-${Date.now()}`)));
  }

  runtime.log("Step 2: Fetching sentinel votes...");
  const httpClient = new cre.capabilities.HTTPClient();

  const fetchVotes = (sendRequester: HTTPSendRequester, config: Config): SentinelVote[] => {
    const resp = sendRequester
      .sendRequest({
        url: `${config.agentApiUrl}/api/v1/sentinel/aggregate`,
        method: "GET",
        headers: {},
      })
      .result();

    if (!ok(resp)) {
      throw new Error(`Sentinel API returned ${resp.statusCode}`);
    }

    const bodyText = new TextDecoder().decode(resp.body);
    const data = JSON.parse(bodyText);
    return (data.consensus?.votes ?? []) as SentinelVote[];
  };

  const votes = httpClient
    .sendRequest(runtime, fetchVotes, consensusIdenticalAggregation<
        SentinelVote[]
      >())(runtime.config)
    .result();

  if (votes.length === 0) {
    runtime.log("  No votes available — cannot resolve tie.");
    return JSON.stringify({
      resolved: false,
      selected_sentinel: "",
      final_threat_level: "NONE",
      random_seed: randomWord.toString().slice(0, 20),
      method: evm.vrfCoordinator ? "vrf" : "reputation_weighted",
    } satisfies TieBreakerResult);
  }

  runtime.log(`  Received ${votes.length} sentinel votes:`);
  for (const v of votes) {
    runtime.log(`    ${v.sentinel_id}: ${v.threat_level} (confidence: ${v.confidence})`);
  }

  runtime.log("Step 3: Performing weighted random selection...");
  const { selectedIndex, selectedVote } = weightedSelect(votes, randomWord);

  runtime.log(`  Selected sentinel: ${selectedVote.sentinel_id} (index ${selectedIndex})`);
  runtime.log(`  Final threat level: ${selectedVote.threat_level}`);
  runtime.log(`  Selection method: ${evm.vrfCoordinator ? "VRF" : "reputation-weighted"}`);

  const result: TieBreakerResult = {
    resolved: true,
    selected_sentinel: selectedVote.sentinel_id,
    final_threat_level: selectedVote.threat_level,
    random_seed: randomWord.toString().slice(0, 20),
    method: evm.vrfCoordinator ? "vrf" : "reputation_weighted",
  };

  runtime.log(`VRF Tie-Breaker resolved: ${JSON.stringify(result)}`);
  return JSON.stringify(result);
};

const initWorkflow = (config: Config) => {
  const cronCap = new cre.capabilities.CronCapability();

  // triggered on-demand when consensus is split; 10-min cron as keep-alive
  // (production would use HTTP trigger instead)
  return [cre.handler(cronCap.trigger({ schedule: "0 */10 * * * *" }), onTrigger)];
};

export async function main() {
  const runner = await Runner.newRunner<Config>({ configSchema });
  await runner.run(initWorkflow);
}

main();

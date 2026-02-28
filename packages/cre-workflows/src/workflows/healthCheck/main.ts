/**
 * AEGIS Health Check Workflow
 *
 * Periodic health check (every 5 minutes) that verifies:
 *  1. Python agent API is responsive
 *  2. All registered sentinels are alive (on-chain liveness via SentinelRegistry)
 *  3. Chainlink Data Feeds are fresh
 *
 * Chainlink services: CRE + Automation + Data Feeds
 */

import {
  cre,
  type Runtime,
  type HTTPSendRequester,
  Runner,
  getNetwork,
  encodeCallMsg,
  bytesToHex,
  ok,
  consensusIdenticalAggregation,
} from "@chainlink/cre-sdk";
import {
  type Address,
  encodeFunctionData,
  decodeFunctionResult,
  zeroAddress,
} from "viem";

import { sentinelRegistryAbi, chainlinkAggregatorAbi } from "../../types/abis";
import { configSchema, type Config, type HealthResponse } from "../../types";

const MAX_INACTIVITY = 300n; // 5 minutes

const onCronTrigger = (runtime: Runtime<Config>): string => {
  runtime.log("AEGIS Health Check starting...");

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

  // ---- Check 1: Agent API health ----
  runtime.log("Check 1: Agent API health...");
  const httpClient = new cre.capabilities.HTTPClient();

  const fetchHealth = (
    sendRequester: HTTPSendRequester,
    config: Config
  ): HealthResponse => {
    const resp = sendRequester
      .sendRequest({
        url: `${config.agentApiUrl}/api/v1/health`,
        method: "GET",
        headers: {},
      })
      .result();

    if (!ok(resp)) {
      return { status: "UNHEALTHY", sentinels: { active: 0, total: 3 }, last_check: 0 };
    }
    const bodyText = new TextDecoder().decode(resp.body);
    return JSON.parse(bodyText) as HealthResponse;
  };

  const health = httpClient
    .sendRequest(
      runtime,
      fetchHealth,
      consensusIdenticalAggregation<HealthResponse>()
    )(runtime.config)
    .result();

  runtime.log(`  Agent API: ${health.status}`);

  // ---- Check 2: On-chain sentinel liveness ----
  runtime.log("Check 2: Sentinel liveness (on-chain)...");
  const activeSentinelsCallData = encodeFunctionData({
    abi: sentinelRegistryAbi,
    functionName: "getActiveSentinels",
  });
  const activeSentinelsResult = evmClient
    .callContract(runtime, {
      call: encodeCallMsg({
        from: zeroAddress,
        to: evm.sentinelRegistryAddress as Address,
        data: activeSentinelsCallData,
      }),
    })
    .result();
  const activeSentinels = decodeFunctionResult({
    abi: sentinelRegistryAbi,
    functionName: "getActiveSentinels",
    data: bytesToHex(activeSentinelsResult.data) as `0x${string}`,
  }) as bigint[];

  let aliveCount = 0;
  for (const tokenId of activeSentinels) {
    const isAliveCallData = encodeFunctionData({
      abi: sentinelRegistryAbi,
      functionName: "isAlive",
      args: [tokenId, MAX_INACTIVITY],
    });
    const isAliveResult = evmClient
      .callContract(runtime, {
        call: encodeCallMsg({
          from: zeroAddress,
          to: evm.sentinelRegistryAddress as Address,
          data: isAliveCallData,
        }),
      })
      .result();
    const alive = decodeFunctionResult({
      abi: sentinelRegistryAbi,
      functionName: "isAlive",
      data: bytesToHex(isAliveResult.data) as `0x${string}`,
    }) as boolean;
    if (alive) aliveCount++;
  }
  runtime.log(
    `  Sentinels: ${aliveCount}/${activeSentinels.length} alive`
  );

  // ---- Check 3: Chainlink Data Feed freshness ----
  runtime.log("Check 3: Chainlink feed freshness...");
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
  const [, , , updatedAt] = decodeFunctionResult({
    abi: chainlinkAggregatorAbi,
    functionName: "latestRoundData",
    data: bytesToHex(priceResult.data) as `0x${string}`,
  }) as [bigint, bigint, bigint, bigint, bigint];

  const feedAge = Math.floor(Date.now() / 1000) - Number(updatedAt);
  const feedFresh = feedAge < 3600;
  runtime.log(
    `  ETH/USD feed age: ${feedAge}s (${feedFresh ? "FRESH" : "STALE"})`
  );

  // ---- Summary ----
  const overallStatus =
    health.status === "HEALTHY" &&
    aliveCount === activeSentinels.length &&
    feedFresh
      ? "HEALTHY"
      : "DEGRADED";

  runtime.log(`Health Check Complete: ${overallStatus}`);

  return JSON.stringify({
    status: overallStatus,
    agentApi: health.status,
    sentinelsAlive: aliveCount,
    sentinelsTotal: activeSentinels.length,
    feedAge,
    feedFresh,
  });
};

const initWorkflow = (config: Config) => {
  const cronCap = new cre.capabilities.CronCapability();
  return [
    cre.handler(
      cronCap.trigger({ schedule: "0 */5 * * * *" }), // Every 5 minutes
      onCronTrigger
    ),
  ];
};

export async function main() {
  const runner = await Runner.newRunner<Config>({ configSchema });
  await runner.run(initWorkflow);
}

main();

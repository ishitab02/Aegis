/**
 * AEGIS CCIP Cross-Chain Alert Workflow
 *
 * Triggered by CircuitBreakerTriggered event on Base Sepolia.
 * Sends a CCIP message to destination chains (Arbitrum Sepolia, Ethereum Sepolia)
 * so protocols deployed on multiple chains can pause simultaneously.
 *
 * Chainlink services demonstrated:
 *  - CRE (this workflow)
 *  - CCIP (cross-chain message)
 *  - Automation (log trigger)
 *
 * CCIP message payload:
 *   abi.encode(address protocol, bytes32 threatId, uint8 threatLevel, uint256 timestamp)
 *
 * The destination receiver contract should decode and call its local CircuitBreaker.
 */

import {
  cre,
  type Runtime,
  type EVMLog,
  Runner,
  getNetwork,
  encodeCallMsg,
  bytesToHex,
  hexToBase64,
  TxStatus,
} from "@chainlink/cre-sdk";
import {
  type Address,
  encodeFunctionData,
  decodeFunctionResult,
  encodeAbiParameters,
  parseAbiParameters,
  decodeEventLog,
  keccak256,
  toHex,
  zeroAddress,
} from "viem";

import { circuitBreakerAbi, ccipRouterAbi, linkTokenAbi } from "../../types/abis";
import { configSchema, type Config, THREAT_LEVEL_UINT8 } from "../../types";

// ============ Constants ============

// CCIP extra args: V1 tag (0x97a657c9) + gasLimit (200_000)
// Pre-encoded for efficiency — see https://docs.chain.link/ccip/best-practices
const CCIP_EXTRA_ARGS =
  "0x97a657c900000000000000000000000000000000000000000000000000000000000030d40" as `0x${string}`;

// ============ Log Trigger Callback ============

const onCircuitBreakerTriggered = (runtime: Runtime<Config>, log: EVMLog): string => {
  runtime.log("AEGIS CCIP: CircuitBreakerTriggered event detected!");

  const evm = runtime.config.evms[0];

  // ---- Validate CCIP configuration ----
  if (!evm.ccipRouter || !evm.ccipDestinationChainSelector || !evm.ccipReceiverAddress) {
    runtime.log("  CCIP not configured — skipping cross-chain alert.");
    return JSON.stringify({ status: "SKIPPED", reason: "CCIP not configured" });
  }

  // ---- Decode the CircuitBreakerTriggered event ----
  const topics = log.topics.map((t) => bytesToHex(t)) as [`0x${string}`, ...`0x${string}`[]];
  const data = bytesToHex(log.data);

  const decoded = decodeEventLog({
    abi: circuitBreakerAbi,
    eventName: "CircuitBreakerTriggered",
    data: data as `0x${string}`,
    topics,
  });

  const protocol = decoded.args.protocol as Address;
  const threatId = decoded.args.threatId as `0x${string}`;
  const threatLevel = Number(decoded.args.threatLevel);
  const timestamp = BigInt(Math.floor(Date.now() / 1000));

  runtime.log(`  Protocol: ${protocol}`);
  runtime.log(`  ThreatId: ${threatId}`);
  runtime.log(`  ThreatLevel: ${threatLevel}`);

  // ---- Build CCIP message payload ----
  runtime.log("Building CCIP cross-chain alert message...");

  const ccipPayload = encodeAbiParameters(
    parseAbiParameters("address protocol, bytes32 threatId, uint8 threatLevel, uint256 timestamp"),
    [protocol, threatId, threatLevel, timestamp],
  );

  const destinationChainSelector = BigInt(evm.ccipDestinationChainSelector);

  // ---- Get network and EVM client ----
  const network = getNetwork({
    chainFamily: "evm",
    chainSelectorName: evm.chainSelectorName,
    isTestnet: true,
  });
  if (!network) throw new Error(`Network not found: ${evm.chainSelectorName}`);

  const evmClient = new cre.capabilities.EVMClient(network.chainSelector.selector);

  // ---- Step 1: Check LINK balance for CCIP fees ----
  runtime.log("Step 1: Checking LINK balance for CCIP fees...");
  if (evm.linkToken) {
    const balanceCallData = encodeFunctionData({
      abi: linkTokenAbi,
      functionName: "balanceOf",
      args: [evm.ccipRouter as Address],
    });
    const balanceResult = evmClient
      .callContract(runtime, {
        call: encodeCallMsg({
          from: zeroAddress,
          to: evm.linkToken as Address,
          data: balanceCallData,
        }),
      })
      .result();
    const balance = decodeFunctionResult({
      abi: linkTokenAbi,
      functionName: "balanceOf",
      data: bytesToHex(balanceResult.data) as `0x${string}`,
    }) as bigint;
    runtime.log(`  LINK balance: ${balance.toString()}`);
  }

  // ---- Step 2: Estimate CCIP fee ----
  runtime.log("Step 2: Estimating CCIP fee...");
  const ccipMessage = {
    receiver: encodeAbiParameters(parseAbiParameters("address"), [
      evm.ccipReceiverAddress as Address,
    ]),
    data: ccipPayload,
    tokenAmounts: [] as { token: Address; amount: bigint }[],
    feeToken: (evm.linkToken ?? zeroAddress) as Address, // Pay in LINK; zeroAddress = native
    extraArgs: CCIP_EXTRA_ARGS,
  };

  const getFeeCallData = encodeFunctionData({
    abi: ccipRouterAbi,
    functionName: "getFee",
    args: [destinationChainSelector, ccipMessage],
  });

  const feeResult = evmClient
    .callContract(runtime, {
      call: encodeCallMsg({
        from: zeroAddress,
        to: evm.ccipRouter as Address,
        data: getFeeCallData,
      }),
    })
    .result();

  const fee = decodeFunctionResult({
    abi: ccipRouterAbi,
    functionName: "getFee",
    data: bytesToHex(feeResult.data) as `0x${string}`,
  }) as bigint;
  runtime.log(`  Estimated CCIP fee: ${fee.toString()} (LINK wei)`);

  // ---- Step 3: Approve LINK spend for router ----
  if (evm.linkToken) {
    runtime.log("Step 3: Approving LINK for CCIP Router...");
    const approveCallData = encodeFunctionData({
      abi: linkTokenAbi,
      functionName: "approve",
      args: [evm.ccipRouter as Address, fee * 2n], // 2x buffer for safety
    });

    const approveReportData = encodeAbiParameters(parseAbiParameters("address to, bytes data"), [
      evm.linkToken as Address,
      approveCallData,
    ]);

    const approveReport = runtime
      .report({
        encodedPayload: hexToBase64(approveReportData),
        encoderName: "evm",
        signingAlgo: "ecdsa",
        hashingAlgo: "keccak256",
      })
      .result();

    const approveResult = evmClient
      .writeReport(runtime, {
        receiver: evm.linkToken as Address,
        report: approveReport,
        gasConfig: { gasLimit: "100000" },
      })
      .result();

    if (approveResult.txStatus === TxStatus.SUCCESS) {
      runtime.log("  LINK approved for CCIP Router.");
    } else {
      runtime.log(`  LINK approval failed: ${approveResult.txStatus}`);
    }
  }

  // ---- Step 4: Send CCIP message ----
  runtime.log("Step 4: Sending CCIP cross-chain alert...");
  const ccipSendCallData = encodeFunctionData({
    abi: ccipRouterAbi,
    functionName: "ccipSend",
    args: [destinationChainSelector, ccipMessage],
  });

  const ccipReportData = encodeAbiParameters(parseAbiParameters("address to, bytes data"), [
    evm.ccipRouter as Address,
    ccipSendCallData,
  ]);

  const ccipReport = runtime
    .report({
      encodedPayload: hexToBase64(ccipReportData),
      encoderName: "evm",
      signingAlgo: "ecdsa",
      hashingAlgo: "keccak256",
    })
    .result();

  const ccipWriteResult = evmClient
    .writeReport(runtime, {
      receiver: evm.ccipRouter as Address,
      report: ccipReport,
      gasConfig: { gasLimit: evm.gasLimit },
    })
    .result();

  if (ccipWriteResult.txStatus === TxStatus.SUCCESS) {
    const txHash = bytesToHex(ccipWriteResult.txHash ?? new Uint8Array(32));
    runtime.log(`  CCIP alert sent! TX: ${txHash}`);
    runtime.log(`  Destination chain: ${evm.ccipDestinationChainSelector}`);
    runtime.log(`  Receiver: ${evm.ccipReceiverAddress}`);

    return JSON.stringify({
      status: "SENT",
      txHash,
      protocol,
      threatId,
      threatLevel,
      destinationChain: evm.ccipDestinationChainSelector,
      estimatedFee: fee.toString(),
    });
  } else {
    runtime.log(`  CCIP send failed: ${ccipWriteResult.txStatus}`);
    return JSON.stringify({
      status: "FAILED",
      error: `TX status: ${ccipWriteResult.txStatus}`,
    });
  }
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

  const evmClient = new cre.capabilities.EVMClient(network.chainSelector.selector);

  // Listen for CircuitBreakerTriggered events
  const eventSignature = "CircuitBreakerTriggered(address,bytes32,uint8,string)";
  const eventHash = keccak256(toHex(eventSignature));

  return [
    cre.handler(
      evmClient.logTrigger({
        addresses: [evm.circuitBreakerAddress],
        topics: [{ values: [eventHash] }],
        confidence: "CONFIDENCE_LEVEL_FINALIZED",
      }),
      onCircuitBreakerTriggered,
    ),
  ];
};

// ============ Entry Point ============

export async function main() {
  const runner = await Runner.newRunner<Config>({ configSchema });
  await runner.run(initWorkflow);
}

main();

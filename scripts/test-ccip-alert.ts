#!/usr/bin/env npx tsx
// AEGIS Protocol — CCIP Cross-Chain Alert Test
// Sends a real CCIP message from Base Sepolia → Arbitrum Sepolia
//
// Usage:
//   npx tsx scripts/test-ccip-alert.ts                          # dry run (fee estimate only)
//   npx tsx scripts/test-ccip-alert.ts --send                   # actually send the message
//   npx tsx scripts/test-ccip-alert.ts --send --receiver=0x...  # send to specific receiver

import { ethers } from "ethers";
import * as dotenv from "dotenv";
dotenv.config();

// ============ Configuration ============

const CONFIG = {
  // Source chain: Base Sepolia
  BASE_SEPOLIA_RPC: process.env.BASE_SEPOLIA_RPC ?? "https://sepolia.base.org",
  PRIVATE_KEY: process.env.DEPLOYER_PRIVATE_KEY ?? "",

  // CCIP Router on Base Sepolia
  // https://docs.chain.link/ccip/directory/testnet/chain/base-testnet-sepolia
  CCIP_ROUTER_BASE_SEPOLIA: "0xD3b06cEbF099CE7DA4AcCf578aaebFDBd6e88a93",

  // Destination: Arbitrum Sepolia chain selector
  // https://docs.chain.link/ccip/directory/testnet/chain/arbitrum-testnet-sepolia
  ARBITRUM_SEPOLIA_CHAIN_SELECTOR: "3478487238524512106",

  // AEGIS contracts on Base Sepolia
  CIRCUIT_BREAKER: process.env.CIRCUIT_BREAKER_ADDRESS ?? "0xa0eE49660252B353830ADe5de0Ca9385647F85b5",
  MOCK_PROTOCOL: process.env.MOCK_PROTOCOL_ADDRESS ?? "0x11887863b89F1bE23A650909135ffaCFab666803",
};

// CCIP extra args: v1 tag (0x97a657c9) + gasLimit 200_000
// See https://docs.chain.link/ccip/best-practices#using-extra-args
const CCIP_EXTRA_ARGS = "0x97a657c9" + "0000000000000000000000000000000000000000000000000000000000030d40";

// ============ ABIs ============

const CCIP_ROUTER_ABI = [
  `function ccipSend(
    uint64 destinationChainSelector,
    tuple(
      bytes receiver,
      bytes data,
      tuple(address token, uint256 amount)[] tokenAmounts,
      address feeToken,
      bytes extraArgs
    ) message
  ) external payable returns (bytes32 messageId)`,

  `function getFee(
    uint64 destinationChainSelector,
    tuple(
      bytes receiver,
      bytes data,
      tuple(address token, uint256 amount)[] tokenAmounts,
      address feeToken,
      bytes extraArgs
    ) message
  ) external view returns (uint256 fee)`,

  // Event emitted by router when message is queued
  "event CCIPSendRequested(tuple(bytes32 messageId, uint64 sourceChainSelector, address sender, tuple(bytes receiver, bytes data, tuple(address token, uint256 amount)[] tokenAmounts, address feeToken, bytes extraArgs) message) message)",
];

// ============ Colour helpers ============

const C = {
  reset: "\x1b[0m",
  bold: "\x1b[1m",
  dim: "\x1b[2m",
  red: "\x1b[31m",
  green: "\x1b[32m",
  yellow: "\x1b[33m",
  cyan: "\x1b[36m",
  magenta: "\x1b[35m",
};

function log(tag: string, msg: string, color: string = C.reset) {
  const ts = new Date().toISOString().split("T")[1].split(".")[0];
  console.log(`${C.dim}[${ts}]${C.reset} ${color}${tag}${C.reset} ${msg}`);
}

function banner() {
  console.log(`
${C.cyan}${C.bold}
  ╔══════════════════════════════════════════════════════════╗
  ║        AEGIS CCIP Cross-Chain Alert Test                 ║
  ║   Base Sepolia ──────────────────▶ Arbitrum Sepolia     ║
  ╚══════════════════════════════════════════════════════════╝
${C.reset}`);
}

// ============ Main ============

async function main() {
  banner();

  const args = process.argv.slice(2);
  const shouldSend = args.includes("--send");
  const receiverArg = args.find((a) => a.startsWith("--receiver="))?.split("=")[1];

  // Parse wallet
  if (!CONFIG.PRIVATE_KEY) {
    log("[ERROR]", "DEPLOYER_PRIVATE_KEY not set in .env", C.red);
    log("[INFO]", "Set it to send real transactions (testnet only)", C.yellow);
    if (shouldSend) process.exit(1);
  }

  const provider = new ethers.JsonRpcProvider(CONFIG.BASE_SEPOLIA_RPC);

  let wallet: ethers.Wallet | null = null;
  let senderAddress = "0x0000000000000000000000000000000000000000";

  if (CONFIG.PRIVATE_KEY) {
    wallet = new ethers.Wallet(CONFIG.PRIVATE_KEY, provider);
    senderAddress = wallet.address;
    log("[INFO]", `Sender wallet: ${senderAddress}`, C.cyan);

    const balance = await provider.getBalance(senderAddress);
    log("[INFO]", `ETH balance: ${ethers.formatEther(balance)} ETH`, C.cyan);

    if (balance === 0n && shouldSend) {
      log("[ERROR]", "Wallet has no ETH. Get testnet ETH from https://www.alchemy.com/faucets/base-sepolia", C.red);
      process.exit(1);
    }
  }

  // The receiver address: use provided arg, sender, or zero address for dry run
  const receiverAddress = receiverArg ?? senderAddress;
  log("[INFO]", `Receiver on Arbitrum Sepolia: ${receiverAddress}`, C.cyan);
  log("[INFO]", `CCIP Router (Base Sepolia): ${CONFIG.CCIP_ROUTER_BASE_SEPOLIA}`, C.dim);
  log("[INFO]", `Destination chain selector: ${CONFIG.ARBITRUM_SEPOLIA_CHAIN_SELECTOR}`, C.dim);

  // ── Encode the AEGIS alert payload ──────────────────────────────────────
  //
  //   The payload encodes a threat alert with:
  //     - protocol:    address of the monitored protocol
  //     - threatId:    unique ID for this threat event
  //     - threatLevel: 4 = CRITICAL
  //     - timestamp:   Unix timestamp
  //     - description: human-readable alert string
  //
  const abiCoder = ethers.AbiCoder.defaultAbiCoder();

  const threatId = ethers.id(`aegis-ccip-test-${Date.now()}`);
  const timestamp = BigInt(Math.floor(Date.now() / 1000));

  const alertPayload = abiCoder.encode(
    ["string", "address", "bytes32", "uint8", "uint256", "string"],
    [
      "AEGIS_THREAT_ALERT",                     // alert type tag
      CONFIG.MOCK_PROTOCOL,                      // monitored protocol
      threatId,                                  // unique threat ID
      4,                                         // threat level (4 = CRITICAL)
      timestamp,                                 // Unix timestamp
      "Flash loan attack detected — TVL dropped 25% in 30 seconds. AEGIS circuit breaker activated.",
    ]
  );

  log("[INFO]", `Alert payload encoded: ${alertPayload.slice(0, 66)}...`, C.dim);
  log("[INFO]", `Threat ID: ${threatId}`, C.dim);
  log("[INFO]", `Timestamp: ${new Date(Number(timestamp) * 1000).toISOString()}`, C.dim);

  // ── Build CCIP message ───────────────────────────────────────────────────

  // receiver is ABI-encoded address (padded to 32 bytes as per CCIP spec)
  const encodedReceiver = abiCoder.encode(["address"], [receiverAddress]);

  const ccipMessage = {
    receiver: encodedReceiver,
    data: alertPayload,
    tokenAmounts: [] as { token: string; amount: bigint }[],  // no tokens, data-only message
    feeToken: ethers.ZeroAddress,                             // pay in native ETH
    extraArgs: CCIP_EXTRA_ARGS,
  };

  // ── Connect to router ────────────────────────────────────────────────────

  const signerOrProvider = wallet ?? provider;
  const router = new ethers.Contract(
    CONFIG.CCIP_ROUTER_BASE_SEPOLIA,
    CCIP_ROUTER_ABI,
    signerOrProvider
  );

  // ── Estimate fee ─────────────────────────────────────────────────────────

  log("[STEP]", "Estimating CCIP fee...", C.magenta);

  let fee: bigint;
  try {
    fee = await router.getFee(BigInt(CONFIG.ARBITRUM_SEPOLIA_CHAIN_SELECTOR), ccipMessage);
    log("[INFO]", `Estimated fee: ${ethers.formatEther(fee)} ETH (${fee.toString()} wei)`, C.green);
  } catch (err: any) {
    log("[ERROR]", `Failed to estimate fee: ${err.message}`, C.red);
    log("[INFO]", "This may mean the CCIP router address is wrong or RPC is unreachable.", C.yellow);
    process.exit(1);
  }

  if (!shouldSend) {
    console.log(`
${C.yellow}${C.bold}--- DRY RUN MODE ---${C.reset}
${C.dim}Run with --send flag to actually send the CCIP message.${C.reset}

${C.bold}Message summary:${C.reset}
  Source chain:       Base Sepolia (84532)
  Destination chain:  Arbitrum Sepolia (${CONFIG.ARBITRUM_SEPOLIA_CHAIN_SELECTOR})
  Receiver:           ${receiverAddress}
  Protocol:           ${CONFIG.MOCK_PROTOCOL}
  Threat level:       4 (CRITICAL)
  Fee:                ${ethers.formatEther(fee)} ETH

${C.bold}Command to send:${C.reset}
  npx tsx scripts/test-ccip-alert.ts --send

${C.bold}Track messages at:${C.reset}
  https://ccip.chain.link
`);
    return;
  }

  // ── Send CCIP message ─────────────────────────────────────────────────────

  if (!wallet) {
    log("[ERROR]", "Cannot send without a wallet. Set DEPLOYER_PRIVATE_KEY.", C.red);
    process.exit(1);
  }

  log("[STEP]", "Sending CCIP cross-chain alert...", C.magenta);
  log("[INFO]", `Paying ${ethers.formatEther(fee)} ETH in fees`, C.dim);

  let tx: ethers.TransactionResponse;
  try {
    tx = await router.ccipSend(
      BigInt(CONFIG.ARBITRUM_SEPOLIA_CHAIN_SELECTOR),
      ccipMessage,
      { value: fee }
    );
  } catch (err: any) {
    log("[ERROR]", `Transaction failed: ${err.message}`, C.red);
    process.exit(1);
  }

  log("[INFO]", `Transaction hash: ${tx.hash}`, C.cyan);
  log("[INFO]", `Base Sepolia explorer: https://sepolia.basescan.org/tx/${tx.hash}`, C.cyan);
  log("[STEP]", "Waiting for confirmation...", C.magenta);

  const receipt = await tx.wait();

  if (!receipt || receipt.status !== 1) {
    log("[ERROR]", "Transaction failed or reverted", C.red);
    process.exit(1);
  }

  log("[SUCCESS]", `Confirmed in block ${receipt.blockNumber}`, C.green);

  // ── Extract CCIP message ID from logs ─────────────────────────────────────
  //
  // The CCIP Router emits the message ID in the CCIPSendRequested event.
  // The first topic[1] on the MessageSent event (keccak256 of "CCIPSendRequested")
  // OR we can grab it from the return value simulation.
  //
  // Simpler: look for 32-byte values in logs that look like message IDs.
  //

  let messageId: string | null = null;

  // Try to decode from router interface
  const routerInterface = new ethers.Interface(CCIP_ROUTER_ABI);
  for (const logEntry of receipt.logs) {
    try {
      const parsed = routerInterface.parseLog({
        topics: logEntry.topics as string[],
        data: logEntry.data,
      });
      if (parsed && parsed.name === "CCIPSendRequested") {
        // The messageId is nested in the message struct
        const msg = parsed.args[0];
        messageId = msg.messageId ?? msg[0];
        break;
      }
    } catch {
      // Not this event, skip
    }
  }

  // Fallback: scan all logs for a 32-byte topic that could be the message ID.
  // CCIP typically emits the message ID as the first indexed topic of its send event.
  if (!messageId) {
    for (const logEntry of receipt.logs) {
      // Router logs will have topics[1] = message ID if first indexed param
      if (
        logEntry.address.toLowerCase() === CONFIG.CCIP_ROUTER_BASE_SEPOLIA.toLowerCase() &&
        logEntry.topics.length >= 2
      ) {
        messageId = logEntry.topics[1];
        break;
      }
    }
  }

  // Print results
  console.log(`
${C.green}${C.bold}
  ╔══════════════════════════════════════════════════════════╗
  ║          CCIP Alert Sent Successfully!                   ║
  ╚══════════════════════════════════════════════════════════╝
${C.reset}
${C.bold}Transaction:${C.reset}
  Hash:         ${tx.hash}
  Block:        ${receipt.blockNumber}
  Gas used:     ${receipt.gasUsed.toString()}
  Fee paid:     ${ethers.formatEther(fee)} ETH

${C.bold}CCIP Message:${C.reset}
  Message ID:   ${messageId ?? "(see logs above — decode from receipt)"}
  Source:       Base Sepolia (84532)
  Destination:  Arbitrum Sepolia (${CONFIG.ARBITRUM_SEPOLIA_CHAIN_SELECTOR})
  Receiver:     ${receiverAddress}

${C.bold}Alert Payload:${C.reset}
  Type:         AEGIS_THREAT_ALERT
  Protocol:     ${CONFIG.MOCK_PROTOCOL}
  Threat level: 4 (CRITICAL)
  Threat ID:    ${threatId}
  Description:  Flash loan attack detected — TVL dropped 25%

${C.bold}Track this message:${C.reset}
  ${messageId
    ? `https://ccip.chain.link/msg/${messageId}`
    : `https://ccip.chain.link (search by TX hash: ${tx.hash})`}

${C.bold}Base Sepolia Explorer:${C.reset}
  https://sepolia.basescan.org/tx/${tx.hash}

${C.dim}The message will arrive on Arbitrum Sepolia in ~5-15 minutes.${C.reset}
`);
}

main().catch((err) => {
  console.error(`\n${C.red}Fatal error:${C.reset}`, err.message ?? err);
  process.exit(1);
});

/**
 * Setup VRF Subscription for AEGIS Protocol
 *
 * This script creates a VRF subscription, adds the consumer, and funds it with LINK.
 *
 * Usage:
 *   npx tsx scripts/setup-vrf-subscription.ts
 *
 * Prerequisites:
 *   - LINK tokens from https://faucets.chain.link/base-sepolia
 *   - DEPLOYER_PRIVATE_KEY in .env
 */

import { createPublicClient, createWalletClient, http, parseAbi, formatEther } from "viem";
import { baseSepolia } from "viem/chains";
import { privateKeyToAccount } from "viem/accounts";
import * as dotenv from "dotenv";

dotenv.config();

// Base Sepolia VRF v2.5 Configuration
const VRF_COORDINATOR = "0x5C210eF41CD1a72de73bF76eC39637bB0d3d7BEE" as const;
const LINK_TOKEN = "0xE4aB69C077896252FAFBD49EFD26B5D171A32410" as const;
const VRF_CONSUMER = "0x51bAC1448E5beC0E78B0408473296039A207255e" as const;

// LINK amount to fund (1 LINK = 10^18)
const LINK_FUND_AMOUNT = BigInt("2000000000000000000"); // 2 LINK

const vrfCoordinatorAbi = parseAbi([
  "function createSubscription() external returns (uint256 subId)",
  "function addConsumer(uint256 subId, address consumer) external",
  "function getSubscription(uint256 subId) view returns (uint96 balance, uint96 nativeBalance, uint64 reqCount, address owner, address[] consumers)",
  "event SubscriptionCreated(uint256 indexed subId, address owner)",
  "event SubscriptionConsumerAdded(uint256 indexed subId, address consumer)",
]);

const linkTokenAbi = parseAbi([
  "function balanceOf(address account) view returns (uint256)",
  "function transferAndCall(address to, uint256 value, bytes calldata data) external returns (bool success)",
  "function approve(address spender, uint256 value) external returns (bool success)",
]);

const vrfConsumerAbi = parseAbi([
  "function setSubscriptionId(uint256 subscriptionId) external",
  "function s_subscriptionId() view returns (uint256)",
]);

async function main() {
  console.log("=== AEGIS VRF Subscription Setup ===\n");

  // Setup clients
  const privateKey = process.env.DEPLOYER_PRIVATE_KEY;
  if (!privateKey) {
    throw new Error("DEPLOYER_PRIVATE_KEY not found in .env");
  }

  const account = privateKeyToAccount(`0x${privateKey.replace("0x", "")}`);

  const publicClient = createPublicClient({
    chain: baseSepolia,
    transport: http("https://sepolia.base.org"),
  });

  const walletClient = createWalletClient({
    account,
    chain: baseSepolia,
    transport: http("https://sepolia.base.org"),
  });

  console.log("Account:", account.address);

  // Check LINK balance
  const linkBalance = await publicClient.readContract({
    address: LINK_TOKEN,
    abi: linkTokenAbi,
    functionName: "balanceOf",
    args: [account.address],
  });

  console.log("LINK Balance:", formatEther(linkBalance), "LINK");

  if (linkBalance < LINK_FUND_AMOUNT) {
    console.log("\n⚠️  Insufficient LINK balance!");
    console.log(`   Need: ${formatEther(LINK_FUND_AMOUNT)} LINK`);
    console.log(`   Have: ${formatEther(linkBalance)} LINK`);
    console.log("\n   Get LINK from: https://faucets.chain.link/base-sepolia");
    console.log("\n   After getting LINK, run this script again.\n");
    process.exit(1);
  }

  // Step 1: Create subscription
  console.log("\n--- Step 1: Creating VRF Subscription ---");

  const createSubTx = await walletClient.writeContract({
    address: VRF_COORDINATOR,
    abi: vrfCoordinatorAbi,
    functionName: "createSubscription",
  });

  console.log("Create subscription TX:", createSubTx);

  const createSubReceipt = await publicClient.waitForTransactionReceipt({
    hash: createSubTx,
  });

  // Parse subscription ID from logs
  const subCreatedLog = createSubReceipt.logs.find(
    (log) =>
      log.topics[0] ===
      "0x464722b4166576d3dcbba877b999bc35cf911f4eaf434b7eba68fa113951d0bf" // SubscriptionCreated event
  );

  let subscriptionId: bigint;
  if (subCreatedLog && subCreatedLog.topics[1]) {
    subscriptionId = BigInt(subCreatedLog.topics[1]);
  } else {
    // Fallback: try to get from return value or use a different method
    console.log("Warning: Could not parse subscription ID from logs, checking return value...");
    // We'll try another approach below
    throw new Error("Could not determine subscription ID");
  }

  console.log("✅ Subscription created! ID:", subscriptionId.toString());

  // Step 2: Fund subscription with LINK using transferAndCall
  console.log("\n--- Step 2: Funding Subscription with LINK ---");

  // Encode the subscription ID for transferAndCall
  const encodedSubId = `0x${subscriptionId.toString(16).padStart(64, "0")}`;

  const fundTx = await walletClient.writeContract({
    address: LINK_TOKEN,
    abi: linkTokenAbi,
    functionName: "transferAndCall",
    args: [VRF_COORDINATOR, LINK_FUND_AMOUNT, encodedSubId as `0x${string}`],
  });

  console.log("Fund subscription TX:", fundTx);

  await publicClient.waitForTransactionReceipt({ hash: fundTx });
  console.log("✅ Funded subscription with", formatEther(LINK_FUND_AMOUNT), "LINK");

  // Step 3: Add consumer to subscription
  console.log("\n--- Step 3: Adding Consumer to Subscription ---");

  const addConsumerTx = await walletClient.writeContract({
    address: VRF_COORDINATOR,
    abi: vrfCoordinatorAbi,
    functionName: "addConsumer",
    args: [subscriptionId, VRF_CONSUMER],
  });

  console.log("Add consumer TX:", addConsumerTx);

  await publicClient.waitForTransactionReceipt({ hash: addConsumerTx });
  console.log("✅ Added consumer:", VRF_CONSUMER);

  // Step 4: Update consumer's subscription ID
  console.log("\n--- Step 4: Updating Consumer's Subscription ID ---");

  const setSubIdTx = await walletClient.writeContract({
    address: VRF_CONSUMER,
    abi: vrfConsumerAbi,
    functionName: "setSubscriptionId",
    args: [subscriptionId],
  });

  console.log("Set subscription ID TX:", setSubIdTx);

  await publicClient.waitForTransactionReceipt({ hash: setSubIdTx });
  console.log("✅ Updated consumer subscription ID");

  // Verify subscription
  console.log("\n--- Verifying Subscription ---");

  const subInfo = await publicClient.readContract({
    address: VRF_COORDINATOR,
    abi: vrfCoordinatorAbi,
    functionName: "getSubscription",
    args: [subscriptionId],
  });

  console.log("\nSubscription Info:");
  console.log("  ID:", subscriptionId.toString());
  console.log("  LINK Balance:", formatEther(subInfo[0]), "LINK");
  console.log("  Native Balance:", formatEther(subInfo[1]), "ETH");
  console.log("  Request Count:", subInfo[2].toString());
  console.log("  Owner:", subInfo[3]);
  console.log("  Consumers:", subInfo[4]);

  // Update .env reminder
  console.log("\n=== Setup Complete ===");
  console.log("\n📝 Update your .env file:");
  console.log(`   CHAINLINK_VRF_SUBSCRIPTION_ID=${subscriptionId.toString()}`);
  console.log("\nYou can now run: npx tsx scripts/test-vrf-request.ts");
}

main().catch((error) => {
  console.error("Error:", error);
  process.exit(1);
});

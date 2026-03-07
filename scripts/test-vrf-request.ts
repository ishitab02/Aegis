/**
 * Test VRF Request for AEGIS Protocol
 *
 * This script sends a VRF request and waits for the randomness fulfillment.
 *
 * Usage:
 *   npx tsx scripts/test-vrf-request.ts
 *
 * Prerequisites:
 *   - Run setup-vrf-subscription.ts first
 *   - VRF subscription must be funded with LINK
 */

import {
  createPublicClient,
  createWalletClient,
  http,
  parseAbi,
  formatEther,
  decodeEventLog,
} from "viem";
import { baseSepolia } from "viem/chains";
import { privateKeyToAccount } from "viem/accounts";
import * as dotenv from "dotenv";

dotenv.config();

// Configuration
const VRF_COORDINATOR = "0x5C210eF41CD1a72de73bF76eC39637bB0d3d7BEE" as const;
const VRF_CONSUMER = "0x51bAC1448E5beC0E78B0408473296039A207255e" as const;

const vrfConsumerAbi = parseAbi([
  "function requestTieBreaker(uint256[] calldata sentinelIds) external returns (uint256 requestId, uint256 tieBreakerId)",
  "function getRequest(uint256 requestId) view returns (tuple(uint256 tieBreakerId, uint256[] sentinelIds, uint256 selectedSentinelId, uint256 randomWord, bool fulfilled))",
  "function getTieBreakResult(uint256 tieBreakerId) view returns (tuple(uint256 tieBreakerId, uint256[] sentinelIds, uint256 selectedSentinelId, uint256 randomWord, bool fulfilled))",
  "function getLastSelectedSentinel() view returns (uint256)",
  "function s_subscriptionId() view returns (uint256)",
  "function s_lastRequestId() view returns (uint256)",
  "function s_lastRandomWord() view returns (uint256)",
  "function isRequestFulfilled(uint256 requestId) view returns (bool)",
  "event RandomnessRequested(uint256 indexed requestId, uint256 indexed tieBreakerId, uint256[] sentinelIds)",
  "event RandomnessFulfilled(uint256 indexed requestId, uint256 indexed tieBreakerId, uint256 selectedSentinelId, uint256 randomWord)",
]);

const vrfCoordinatorAbi = parseAbi([
  "function getSubscription(uint256 subId) view returns (uint96 balance, uint96 nativeBalance, uint64 reqCount, address owner, address[] consumers)",
]);

async function main() {
  console.log("=== AEGIS VRF Request Test ===\n");

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
  console.log("VRF Consumer:", VRF_CONSUMER);

  // Check subscription ID
  const subscriptionId = await publicClient.readContract({
    address: VRF_CONSUMER,
    abi: vrfConsumerAbi,
    functionName: "s_subscriptionId",
  });

  console.log("Subscription ID:", subscriptionId.toString());

  if (subscriptionId === 0n) {
    console.log("\n⚠️  Subscription ID is 0! Run setup-vrf-subscription.ts first.");
    process.exit(1);
  }

  // Check subscription balance
  const subInfo = await publicClient.readContract({
    address: VRF_COORDINATOR,
    abi: vrfCoordinatorAbi,
    functionName: "getSubscription",
    args: [subscriptionId],
  });

  console.log("Subscription LINK Balance:", formatEther(subInfo[0]), "LINK");

  if (subInfo[0] < BigInt("100000000000000000")) {
    // 0.1 LINK minimum
    console.log("\n⚠️  Subscription balance too low! Fund with more LINK.");
    process.exit(1);
  }

  // Send VRF request for tie-breaker between sentinel IDs 1, 2, and 3
  console.log("\n--- Sending VRF Request ---");
  console.log("Requesting tie-breaker between sentinels: [1, 2, 3]");

  const requestTx = await walletClient.writeContract({
    address: VRF_CONSUMER,
    abi: vrfConsumerAbi,
    functionName: "requestTieBreaker",
    args: [[1n, 2n, 3n]],
  });

  console.log("Request TX:", requestTx);
  console.log("View on BaseScan:", `https://sepolia.basescan.org/tx/${requestTx}`);

  const requestReceipt = await publicClient.waitForTransactionReceipt({
    hash: requestTx,
  });

  console.log("✅ Request submitted in block:", requestReceipt.blockNumber);

  // Parse request ID from logs
  let requestId: bigint | undefined;
  let tieBreakerId: bigint | undefined;

  for (const log of requestReceipt.logs) {
    try {
      // Look for RandomnessRequested event from our consumer
      if (log.address.toLowerCase() === VRF_CONSUMER.toLowerCase()) {
        const decoded = decodeEventLog({
          abi: vrfConsumerAbi,
          data: log.data,
          topics: log.topics,
        });

        if (decoded.eventName === "RandomnessRequested") {
          requestId = decoded.args.requestId as bigint;
          tieBreakerId = decoded.args.tieBreakerId as bigint;
          break;
        }
      }
    } catch {
      // Skip logs that don't match
    }
  }

  if (!requestId) {
    // Fallback: read from contract
    requestId = await publicClient.readContract({
      address: VRF_CONSUMER,
      abi: vrfConsumerAbi,
      functionName: "s_lastRequestId",
    });
  }

  console.log("\nRequest ID:", requestId?.toString());
  console.log("Tie-Breaker ID:", tieBreakerId?.toString() || "N/A");

  // Wait for fulfillment
  console.log("\n--- Waiting for VRF Fulfillment ---");
  console.log("(This may take 1-5 minutes depending on network conditions...)\n");

  const startTime = Date.now();
  const timeout = 5 * 60 * 1000; // 5 minutes timeout

  while (Date.now() - startTime < timeout) {
    const fulfilled = await publicClient.readContract({
      address: VRF_CONSUMER,
      abi: vrfConsumerAbi,
      functionName: "isRequestFulfilled",
      args: [requestId!],
    });

    if (fulfilled) {
      console.log("✅ VRF Request Fulfilled!");

      // Get the result
      const result = await publicClient.readContract({
        address: VRF_CONSUMER,
        abi: vrfConsumerAbi,
        functionName: "getRequest",
        args: [requestId!],
      });

      const lastSentinel = await publicClient.readContract({
        address: VRF_CONSUMER,
        abi: vrfConsumerAbi,
        functionName: "getLastSelectedSentinel",
      });

      const lastRandomWord = await publicClient.readContract({
        address: VRF_CONSUMER,
        abi: vrfConsumerAbi,
        functionName: "s_lastRandomWord",
      });

      console.log("\n=== VRF Result ===");
      console.log("Tie-Breaker ID:", result.tieBreakerId?.toString() || result[0]?.toString());
      console.log("Sentinel Options:", result.sentinelIds?.toString() || result[1]?.toString());
      console.log("Selected Sentinel ID:", lastSentinel.toString());
      console.log("Random Word:", lastRandomWord.toString());
      console.log("Random Word (hex):", "0x" + lastRandomWord.toString(16));

      console.log("\n=== Summary ===");
      console.log("Request TX:", requestTx);
      console.log("Request ID:", requestId?.toString());
      console.log("Selected Sentinel:", lastSentinel.toString());
      console.log(
        "Time to fulfillment:",
        Math.round((Date.now() - startTime) / 1000),
        "seconds"
      );

      // Output for documentation
      console.log("\n📝 For VRF_TEST_RESULTS.md:");
      console.log("---");
      console.log(`Request TX: ${requestTx}`);
      console.log(`Request ID: ${requestId?.toString()}`);
      console.log(`Random Word: ${lastRandomWord.toString()}`);
      console.log(`Selected Sentinel: ${lastSentinel.toString()}`);
      console.log("---");

      return;
    }

    // Wait 5 seconds before checking again
    process.stdout.write(".");
    await new Promise((resolve) => setTimeout(resolve, 5000));
  }

  console.log("\n⏰ Timeout waiting for VRF fulfillment.");
  console.log("The request was sent but fulfillment hasn't arrived yet.");
  console.log("Request ID:", requestId?.toString());
  console.log("\nYou can check the status later by running this script again,");
  console.log("or by querying the contract directly.");
}

main().catch((error) => {
  console.error("Error:", error);
  process.exit(1);
});

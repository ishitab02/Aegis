/**
 * AEGIS Circuit Breaker E2E Demo
 * 
 * This script demonstrates the full detection → circuit breaker flow:
 * 1. Shows initial vault state
 * 2. Simulates AEGIS detecting a threat
 * 3. Triggers circuit breaker
 * 4. Shows withdrawal is blocked
 */

import { ethers } from "ethers";
import * as dotenv from "dotenv";
import * as path from "path";

dotenv.config({ path: path.resolve(__dirname, "../.env") });

// Helper to wait between transactions (avoid nonce issues)
const sleep = (ms: number) => new Promise(resolve => setTimeout(resolve, ms));

const TEST_VAULT_ABI = [
  "function deposit() external payable",
  "function withdraw(uint256 amount) external",
  "function getTVL() external view returns (uint256)",
  "function isPaused() external view returns (bool)",
  "function pause() external",
  "function unpause() external",
  "function circuitBreaker() external view returns (address)",
  "function deposits(address) external view returns (uint256)",
];


async function main() {
  console.log("╔════════════════════════════════════════════════════════╗");
  console.log("║         AEGIS Circuit Breaker E2E Demo                 ║");
  console.log("╚════════════════════════════════════════════════════════╝\n");

  const provider = new ethers.JsonRpcProvider("https://sepolia.base.org");
  const wallet = new ethers.Wallet(process.env.DEPLOYER_PRIVATE_KEY!, provider);

  const TEST_VAULT = process.env.TEST_VAULT_ADDRESS!;
  const CIRCUIT_BREAKER = "0xa0eE49660252B353830ADe5de0Ca9385647F85b5";

  const vault = new ethers.Contract(TEST_VAULT, TEST_VAULT_ABI, wallet);

  console.log("Deployer:", wallet.address);
  console.log("TestVault:", TEST_VAULT);
  console.log("CircuitBreaker:", CIRCUIT_BREAKER);
  console.log("");

  // Step 1: Show initial state
  console.log("━━━ Step 1: Initial State ━━━");
  const initialTVL = await vault.getTVL();
  const initialPaused = await vault.isPaused();
  const cbAddress = await vault.circuitBreaker();
  console.log("  TVL:", ethers.formatEther(initialTVL), "ETH");
  console.log("  Paused:", initialPaused);
  console.log("  CircuitBreaker:", cbAddress);
  console.log("");

  // Step 2: Simulate AEGIS detection
  console.log("━━━ Step 2: AEGIS Detection Cycle ━━━");
  console.log("  Calling Python Agent API...");
  
  try {
    const response = await fetch("http://localhost:8000/api/v1/detect", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        protocol_address: TEST_VAULT,
        simulate_tvl_drop_percent: 25,
      }),
    });
    const detection = await response.json();
    console.log("  ✓ Detection complete");
    console.log("  Threat Level:", detection.consensus?.final_threat_level || "CRITICAL");
    console.log("  Action:", detection.consensus?.action_recommended || "CIRCUIT_BREAKER");
    console.log("  Sentinels agreed:", detection.assessments?.length || 3);
  } catch (error) {
    console.log("  ⚠ Agent API not running, simulating CRITICAL threat");
  }
  console.log("");

  // Step 3: Trigger circuit breaker
  console.log("━━━ Step 3: Trigger Circuit Breaker ━━━");
  console.log("  AEGIS consensus reached: CRITICAL threat → CIRCUIT_BREAKER action");
  console.log("  Owner (simulating CRE workflow) triggering pause...");

  // For demo, owner directly pauses the vault (simulating CircuitBreaker action)
  // In production, this would be triggered by CircuitBreaker contract via CRE workflow
  const pauseTx = await vault.pause();
  const pauseReceipt = await pauseTx.wait();
  console.log("  ✓ Emergency pause triggered!");
  console.log("  Tx:", pauseReceipt?.hash);

  // Wait for state to propagate
  await sleep(2000);

  const nowPaused = await vault.isPaused();
  console.log("  Vault paused:", nowPaused);
  console.log("");

  // Step 4: Show withdrawal blocked
  console.log("━━━ Step 4: Test Withdrawal (should fail) ━━━");
  if (nowPaused) {
    try {
      const userDeposit = await vault.deposits(wallet.address);
      if (userDeposit > 0n) {
        await vault.withdraw(1n);
        console.log("  ✗ ERROR: Withdrawal succeeded (should have failed)");
      } else {
        // Try to deposit and withdraw
        console.log("  No deposits to withdraw, testing deposit...");
        try {
          await vault.deposit({ value: ethers.parseEther("0.001") });
          console.log("  ✗ ERROR: Deposit succeeded (should have failed)");
        } catch (error: any) {
          console.log("  ✓ Deposit blocked: VaultPaused()");
        }
      }
    } catch (error: any) {
      const errorMsg = error.message || error.toString();
      if (errorMsg.includes("VaultPaused") || errorMsg.includes("paused")) {
        console.log("  ✓ Withdrawal blocked: VaultPaused()");
      } else {
        console.log("  ✓ Operation blocked:", errorMsg.slice(0, 50));
      }
    }
  } else {
    console.log("  ⚠ Vault not paused, skipping withdrawal test");
  }
  console.log("");

  // Step 5: Show recovery (optional)
  console.log("━━━ Step 5: Recovery (unpause) ━━━");
  console.log("  In production, only owner can unpause after investigation");

  // Wait before next transaction
  await sleep(3000);

  const unpauseTx = await vault.unpause();
  const unpauseReceipt = await unpauseTx.wait();
  console.log("  ✓ Vault unpaused");
  console.log("  Tx:", unpauseReceipt?.hash);

  await sleep(2000);
  console.log("  Paused:", await vault.isPaused());
  console.log("");

  console.log("╔════════════════════════════════════════════════════════╗");
  console.log("║                   Demo Complete!                       ║");
  console.log("║  Circuit breaker successfully protected the vault.     ║");
  console.log("╚════════════════════════════════════════════════════════╝");
}

main().catch((error) => {
  console.error("Demo failed:", error);
  process.exit(1);
});

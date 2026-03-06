#!/usr/bin/env npx tsx
/**
 * register-test-vault.ts
 *
 * Register the TestVault with the existing CircuitBreaker contract on Base Sepolia.
 * Also grants CRE_WORKFLOW_ROLE to the deployer for demo purposes.
 *
 * Usage:
 *   TEST_VAULT_ADDRESS=0x... npx tsx scripts/register-test-vault.ts
 *
 * Prerequisites:
 *   - DEPLOYER_PRIVATE_KEY set in env or .env
 *   - TestVault deployed (via DeployTestVault.s.sol)
 */

import { ethers } from "ethers";
import * as dotenv from "dotenv";
dotenv.config();

// ── Configuration ──────────────────────────────────────────────────────────

const RPC_URL = process.env.BASE_SEPOLIA_RPC ?? "https://sepolia.base.org";
const PRIVATE_KEY = process.env.DEPLOYER_PRIVATE_KEY;
const TEST_VAULT = process.env.TEST_VAULT_ADDRESS;
const CIRCUIT_BREAKER = process.env.CIRCUIT_BREAKER_ADDRESS ?? "0xa0eE49660252B353830ADe5de0Ca9385647F85b5";

if (!PRIVATE_KEY) {
  console.error("ERROR: DEPLOYER_PRIVATE_KEY not set");
  process.exit(1);
}
if (!TEST_VAULT) {
  console.error("ERROR: TEST_VAULT_ADDRESS not set");
  console.error("  Deploy the TestVault first:");
  console.error("  forge script script/DeployTestVault.s.sol --rpc-url $BASE_SEPOLIA_RPC --broadcast");
  process.exit(1);
}

// ── ABIs ───────────────────────────────────────────────────────────────────

const CIRCUIT_BREAKER_ABI = [
  "function registerProtocol(address protocol) external",
  "function isRegistered(address protocol) external view returns (bool)",
  "function isPaused(address protocol) external view returns (bool)",
  "function CRE_WORKFLOW_ROLE() external view returns (bytes32)",
  "function hasRole(bytes32 role, address account) external view returns (bool)",
  "function grantRole(bytes32 role, address account) external",
];

const TEST_VAULT_ABI = [
  "function getTVL() external view returns (uint256)",
  "function isPaused() external view returns (bool)",
  "function circuitBreaker() external view returns (address)",
];

// ── Main ───────────────────────────────────────────────────────────────────

async function main() {
  console.log("=== AEGIS: Register TestVault with CircuitBreaker ===\n");

  const provider = new ethers.JsonRpcProvider(RPC_URL);
  const wallet = new ethers.Wallet(PRIVATE_KEY!, provider);
  console.log("Deployer:        ", wallet.address);
  console.log("TestVault:       ", TEST_VAULT);
  console.log("CircuitBreaker:  ", CIRCUIT_BREAKER);

  const breaker = new ethers.Contract(CIRCUIT_BREAKER, CIRCUIT_BREAKER_ABI, wallet);
  const vault = new ethers.Contract(TEST_VAULT!, TEST_VAULT_ABI, provider);

  // Verify TestVault points to the right CircuitBreaker
  const vaultBreaker = await vault.circuitBreaker();
  console.log("\nTestVault.circuitBreaker:", vaultBreaker);
  if (vaultBreaker.toLowerCase() !== CIRCUIT_BREAKER.toLowerCase()) {
    console.warn("WARNING: TestVault doesn't point to the expected CircuitBreaker!");
  }

  // Step 1: Register protocol
  const isRegistered = await breaker.isRegistered(TEST_VAULT);
  if (isRegistered) {
    console.log("\n[SKIP] TestVault already registered in CircuitBreaker");
  } else {
    console.log("\nRegistering TestVault in CircuitBreaker...");
    const tx = await breaker.registerProtocol(TEST_VAULT);
    console.log("  tx:", tx.hash);
    await tx.wait();
    console.log("[OK] TestVault registered!");
  }

  // Step 2: Grant CRE_WORKFLOW_ROLE to deployer (for demo)
  const creRole = await breaker.CRE_WORKFLOW_ROLE();
  const hasRole = await breaker.hasRole(creRole, wallet.address);
  if (hasRole) {
    console.log("[SKIP] Deployer already has CRE_WORKFLOW_ROLE");
  } else {
    console.log("\nGranting CRE_WORKFLOW_ROLE to deployer...");
    const tx = await breaker.grantRole(creRole, wallet.address);
    console.log("  tx:", tx.hash);
    await tx.wait();
    console.log("[OK] CRE_WORKFLOW_ROLE granted!");
  }

  // Step 3: Print status
  const tvl = await vault.getTVL();
  const paused = await vault.isPaused();
  const registered = await breaker.isRegistered(TEST_VAULT);

  console.log("\n=== Status ===");
  console.log("  Registered:", registered);
  console.log("  TVL:       ", ethers.formatEther(tvl), "ETH");
  console.log("  Paused:    ", paused);
  console.log("\nReady for demo! Run:");
  console.log("  npx tsx scripts/demo-circuit-breaker.ts");
}

main().catch((err) => {
  console.error("\nFailed:", err.message ?? err);
  process.exit(1);
});

// SPDX-License-Identifier: MIT
pragma solidity ^0.8.24;

import "forge-std/Script.sol";
import "../src/core/CircuitBreaker.sol";
import "../src/core/SentinelRegistry.sol";
import "../src/core/ThreatReport.sol";
import "../src/core/ReputationTracker.sol";

/**
 * @title IntegrateProtocol
 * @notice Registers a protocol with AEGIS and grants CRE workflow permissions.
 *
 * This script:
 *   1. Registers the MockProtocol in CircuitBreaker (if not already registered)
 *   2. Grants CRE_WORKFLOW_ROLE to the CRE workflow address
 *   3. Registers 3 sentinel agents in SentinelRegistry (if not already done)
 *   4. Authorizes the CRE workflow in ReputationTracker
 *
 * Usage:
 *   CRE_WORKFLOW_ADDRESS=0x... forge script script/IntegrateProtocol.s.sol:IntegrateProtocol \
 *     --rpc-url $BASE_SEPOLIA_RPC \
 *     --private-key $DEPLOYER_PRIVATE_KEY \
 *     --broadcast
 */
contract IntegrateProtocol is Script {
    // ============ Deployed Contract Addresses (Base Sepolia) ============

    address constant SENTINEL_REGISTRY = 0xd34FC1ee378F342EFb92C0D334362B9E577b489f;
    address constant CIRCUIT_BREAKER   = 0xa0eE49660252B353830ADe5de0Ca9385647F85b5;
    address constant THREAT_REPORT     = 0x3f01beefA5b7F5931B5545BbCFCF0a72c7131499;
    address constant REPUTATION_TRACKER = 0x7970433B694f7fa6f8D511c7B20110ECd28db100;
    address constant MOCK_PROTOCOL     = 0x11887863b89F1bE23A650909135ffaCFab666803;

    function run() external {
        uint256 deployerKey = vm.envUint("DEPLOYER_PRIVATE_KEY");
        address creWorkflow = vm.envOr("CRE_WORKFLOW_ADDRESS", address(0));

        vm.startBroadcast(deployerKey);

        // ---- 1. Register MockProtocol in CircuitBreaker ----
        CircuitBreaker breaker = CircuitBreaker(CIRCUIT_BREAKER);

        if (!breaker.isRegistered(MOCK_PROTOCOL)) {
            breaker.registerProtocol(MOCK_PROTOCOL);
            console.log("[OK] MockProtocol registered in CircuitBreaker");
        } else {
            console.log("[SKIP] MockProtocol already registered");
        }

        // ---- 2. Grant CRE_WORKFLOW_ROLE ----
        if (creWorkflow != address(0)) {
            bytes32 creRole = breaker.CRE_WORKFLOW_ROLE();

            if (!breaker.hasRole(creRole, creWorkflow)) {
                breaker.grantRole(creRole, creWorkflow);
                console.log("[OK] CRE_WORKFLOW_ROLE granted to:", creWorkflow);
            } else {
                console.log("[SKIP] CRE_WORKFLOW_ROLE already granted");
            }
        } else {
            console.log("[SKIP] CRE_WORKFLOW_ADDRESS not set - skipping role grant");
        }

        // ---- 3. Register 3 sentinel agents in SentinelRegistry ----
        SentinelRegistry registry = SentinelRegistry(SENTINEL_REGISTRY);
        address operator = vm.addr(deployerKey);

        // Check if sentinels are already registered by looking at operator's list
        uint256[] memory existing = registry.getOperatorSentinels(operator);

        if (existing.length == 0) {
            // Register Liquidity Sentinel
            uint256 liquidityId = registry.registerSentinel(
                ISentinelRegistry.SentinelType.LIQUIDITY,
                operator,
                "ipfs://QmAEGIS/sentinel/liquidity-1.json"
            );
            console.log("[OK] Liquidity Sentinel registered, tokenId:", liquidityId);

            // Register Oracle Sentinel
            uint256 oracleId = registry.registerSentinel(
                ISentinelRegistry.SentinelType.ORACLE,
                operator,
                "ipfs://QmAEGIS/sentinel/oracle-1.json"
            );
            console.log("[OK] Oracle Sentinel registered, tokenId:", oracleId);

            // Register Governance Sentinel
            uint256 govId = registry.registerSentinel(
                ISentinelRegistry.SentinelType.GOVERNANCE,
                operator,
                "ipfs://QmAEGIS/sentinel/governance-1.json"
            );
            console.log("[OK] Governance Sentinel registered, tokenId:", govId);
        } else {
            console.log("[SKIP] Sentinels already registered, count:", existing.length);
        }

        // ---- 4. Authorize CRE workflow in ReputationTracker ----
        ReputationTracker reputation = ReputationTracker(REPUTATION_TRACKER);

        if (creWorkflow != address(0) && !reputation.authorizedUpdaters(creWorkflow)) {
            reputation.addUpdater(creWorkflow);
            console.log("[OK] CRE workflow authorized in ReputationTracker");
        }

        vm.stopBroadcast();

        // ---- Summary ----
        console.log("");
        console.log("=== Integration Summary ===");
        console.log("CircuitBreaker:     ", CIRCUIT_BREAKER);
        console.log("SentinelRegistry:   ", SENTINEL_REGISTRY);
        console.log("ThreatReport:       ", THREAT_REPORT);
        console.log("ReputationTracker:  ", REPUTATION_TRACKER);
        console.log("MockProtocol:       ", MOCK_PROTOCOL);
        console.log("CRE Workflow:       ", creWorkflow);
        console.log("Operator:           ", operator);
    }
}

/**
 * @title ConfigureCircuitBreaker
 * @notice Standalone helper to configure CircuitBreaker parameters.
 *
 * Usage:
 *   forge script script/IntegrateProtocol.s.sol:ConfigureCircuitBreaker \
 *     --rpc-url $BASE_SEPOLIA_RPC \
 *     --private-key $DEPLOYER_PRIVATE_KEY \
 *     --broadcast
 */
contract ConfigureCircuitBreaker is Script {
    address constant CIRCUIT_BREAKER = 0xa0eE49660252B353830ADe5de0Ca9385647F85b5;

    function run() external {
        uint256 deployerKey = vm.envUint("DEPLOYER_PRIVATE_KEY");
        vm.startBroadcast(deployerKey);

        CircuitBreaker breaker = CircuitBreaker(CIRCUIT_BREAKER);

        // Verify current state
        bool paused = breaker.isPaused(0x11887863b89F1bE23A650909135ffaCFab666803);
        console.log("MockProtocol paused:", paused);

        uint256 cooldown = breaker.cooldownPeriod();
        console.log("Cooldown period:", cooldown, "seconds");

        uint256 threshold = breaker.autoPauseThreshold();
        console.log("Auto-pause threshold:", threshold, "HIGH alerts");

        vm.stopBroadcast();
    }
}

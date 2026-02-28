// SPDX-License-Identifier: MIT
pragma solidity ^0.8.24;

import "forge-std/Script.sol";
import "../src/core/SentinelRegistry.sol";
import "../src/core/CircuitBreaker.sol";
import "../src/core/ThreatReport.sol";
import "../src/core/ReputationTracker.sol";
import "../src/mocks/MockProtocol.sol";

/**
 * @title DeployAegis
 * @notice Deploy all AEGIS Protocol contracts
 *
 * Usage:
 *   forge script script/Deploy.s.sol:DeployAegis \
 *     --rpc-url $BASE_SEPOLIA_RPC \
 *     --private-key $DEPLOYER_PRIVATE_KEY \
 *     --broadcast --verify
 */
contract DeployAegis is Script {
    function run() external {
        vm.startBroadcast();

        // 1. Deploy SentinelRegistry
        SentinelRegistry registry = new SentinelRegistry();
        console.log("SentinelRegistry deployed at:", address(registry));

        // 2. Deploy CircuitBreaker
        CircuitBreaker breaker = new CircuitBreaker();
        console.log("CircuitBreaker deployed at:", address(breaker));

        // 3. Deploy ThreatReport (with deployer as initial CRE workflow)
        ThreatReport threatReport = new ThreatReport(msg.sender);
        console.log("ThreatReport deployed at:", address(threatReport));

        // 4. Deploy ReputationTracker
        ReputationTracker reputation = new ReputationTracker();
        console.log("ReputationTracker deployed at:", address(reputation));

        // 5. Deploy MockProtocol (for testing)
        MockProtocol mockProtocol = new MockProtocol();
        console.log("MockProtocol deployed at:", address(mockProtocol));

        // 6. Register mock protocol in CircuitBreaker
        breaker.registerProtocol(address(mockProtocol));
        console.log("MockProtocol registered in CircuitBreaker");

        vm.stopBroadcast();

        console.log("");
        console.log("=== Deployment Summary ===");
        console.log("SentinelRegistry:   ", address(registry));
        console.log("CircuitBreaker:     ", address(breaker));
        console.log("ThreatReport:       ", address(threatReport));
        console.log("ReputationTracker:  ", address(reputation));
        console.log("MockProtocol:       ", address(mockProtocol));
    }
}

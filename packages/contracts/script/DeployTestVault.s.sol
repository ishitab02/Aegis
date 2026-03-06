// SPDX-License-Identifier: MIT
pragma solidity ^0.8.24;

import "forge-std/Script.sol";
import "../src/mocks/TestVault.sol";

contract DeployTestVault is Script {
    // Existing CircuitBreaker on Base Sepolia
    address constant CIRCUIT_BREAKER = 0xa0eE49660252B353830ADe5de0Ca9385647F85b5;

    function run() external {
        uint256 deployerKey = vm.envUint("DEPLOYER_PRIVATE_KEY");
        vm.startBroadcast(deployerKey);

        TestVault vault = new TestVault(CIRCUIT_BREAKER);
        console.log("TestVault deployed to:", address(vault));
        console.log("CircuitBreaker set to:", CIRCUIT_BREAKER);

        vm.stopBroadcast();
    }
}

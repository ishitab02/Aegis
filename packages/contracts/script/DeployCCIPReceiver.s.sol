// SPDX-License-Identifier: MIT
pragma solidity ^0.8.24;

import "forge-std/Script.sol";
import "../src/ccip/AlertReceiver.sol";

/**
 * @title DeployCCIPReceiver
 * @notice Deploys AlertReceiver to Arbitrum Sepolia for CCIP cross-chain alert demo.
 *
 * Usage:
 *   forge script script/DeployCCIPReceiver.s.sol:DeployCCIPReceiver \
 *     --rpc-url https://sepolia-rollup.arbitrum.io/rpc \
 *     --private-key $DEPLOYER_PRIVATE_KEY \
 *     --broadcast
 *
 * After deployment:
 *   1. Copy the deployed address
 *   2. Run the CCIP test with the receiver:
 *      npx tsx scripts/test-ccip-alert.ts --send --receiver=<deployed-address>
 */
contract DeployCCIPReceiver is Script {
    // Chainlink CCIP Router on Arbitrum Sepolia
    // See: https://docs.chain.link/ccip/directory/testnet/chain/arbitrum-testnet-sepolia
    address constant CCIP_ROUTER_ARBITRUM_SEPOLIA = 0x2a9C5afB0d0e4BAb2BCdaE109EC4b0c4Be15a165;

    function run() external {
        uint256 deployerKey = vm.envUint("DEPLOYER_PRIVATE_KEY");
        address deployer = vm.addr(deployerKey);

        console.log("Deploying AlertReceiver to Arbitrum Sepolia...");
        console.log("Deployer:    ", deployer);
        console.log("CCIP Router: ", CCIP_ROUTER_ARBITRUM_SEPOLIA);

        vm.startBroadcast(deployerKey);

        AlertReceiver receiver = new AlertReceiver(CCIP_ROUTER_ARBITRUM_SEPOLIA);

        vm.stopBroadcast();

        console.log("");
        console.log("=== Deployment Complete ===");
        console.log("AlertReceiver:", address(receiver));
        console.log("");
        console.log("Next steps:");
        console.log("1. Save this address in .env as CCIP_RECEIVER_ADDRESS");
        console.log("2. Send a test alert:");
        console.log("   npx tsx scripts/test-ccip-alert.ts --send --receiver=", address(receiver));
        console.log("3. Track the message at https://ccip.chain.link");
        console.log("4. Verify receipt on Arbitrum Sepolia explorer:");
        console.log("   https://sepolia.arbiscan.io/address/", address(receiver));
    }
}

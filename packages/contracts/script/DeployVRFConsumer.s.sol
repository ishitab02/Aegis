// SPDX-License-Identifier: MIT
pragma solidity ^0.8.24;

import "forge-std/Script.sol";
import "../src/vrf/AegisVRFConsumer.sol";

/**
 * @title DeployVRFConsumer
 * @notice Deploy AEGIS VRF Consumer contract to Base Sepolia
 *
 * Base Sepolia VRF v2.5 Configuration:
 * - VRF Coordinator: 0x5C210eF41CD1a72de73bF76eC39637bB0d3d7BEE
 * - LINK Token: 0xE4aB69C077896252FAFBD49EFD26B5D171A32410
 * - Key Hash (500 gwei): 0x9e9e46732b32662b9adc6f3abdf6c5e926a666d174a4d6b8e39c4cca76a38897
 *
 * Usage (without subscription - creates with subId 0):
 *   forge script script/DeployVRFConsumer.s.sol:DeployVRFConsumer \
 *     --rpc-url https://sepolia.base.org \
 *     --private-key $DEPLOYER_PRIVATE_KEY \
 *     --broadcast
 *
 * Usage (with subscription):
 *   VRF_SUBSCRIPTION_ID=123 forge script script/DeployVRFConsumer.s.sol:DeployVRFConsumer \
 *     --rpc-url https://sepolia.base.org \
 *     --private-key $DEPLOYER_PRIVATE_KEY \
 *     --broadcast
 */
contract DeployVRFConsumer is Script {
    // Base Sepolia VRF v2.5 configuration
    address constant VRF_COORDINATOR = 0x5C210eF41CD1a72de73bF76eC39637bB0d3d7BEE;
    bytes32 constant KEY_HASH = 0x9e9e46732b32662b9adc6f3abdf6c5e926a666d174a4d6b8e39c4cca76a38897;

    // Default VRF parameters
    uint32 constant CALLBACK_GAS_LIMIT = 100000;
    uint16 constant REQUEST_CONFIRMATIONS = 3;

    function run() external {
        // Get subscription ID from environment (0 if not set)
        uint256 subscriptionId = vm.envOr("VRF_SUBSCRIPTION_ID", uint256(0));

        console.log("=== AEGIS VRF Consumer Deployment ===");
        console.log("");
        console.log("VRF Coordinator:", VRF_COORDINATOR);
        console.log("Key Hash:", vm.toString(KEY_HASH));
        console.log("Subscription ID:", subscriptionId);
        console.log("Callback Gas Limit:", CALLBACK_GAS_LIMIT);
        console.log("Request Confirmations:", REQUEST_CONFIRMATIONS);
        console.log("");

        vm.startBroadcast();

        AegisVRFConsumer consumer =
            new AegisVRFConsumer(VRF_COORDINATOR, KEY_HASH, subscriptionId, CALLBACK_GAS_LIMIT, REQUEST_CONFIRMATIONS);

        console.log("AegisVRFConsumer deployed at:", address(consumer));

        vm.stopBroadcast();

        console.log("");
        console.log("=== Deployment Complete ===");
        console.log("Consumer Address:", address(consumer));
        console.log("");
        console.log("Next steps:");
        if (subscriptionId == 0) {
            console.log("1. Create a VRF subscription at https://vrf.chain.link/base-sepolia");
            console.log("2. Fund it with LINK tokens");
            console.log("3. Add this consumer address to the subscription");
            console.log("4. Update the subscription ID: consumer.setSubscriptionId(YOUR_SUB_ID)");
        } else {
            console.log("1. Ensure subscription", subscriptionId, "is funded with LINK");
            console.log("2. Add this consumer address to the subscription at https://vrf.chain.link/base-sepolia");
        }
    }
}

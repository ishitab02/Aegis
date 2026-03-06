// SPDX-License-Identifier: MIT
pragma solidity ^0.8.24;

import "forge-std/Script.sol";

interface IVRFCoordinatorV2Plus {
    function createSubscription() external returns (uint256 subId);
    function addConsumer(uint256 subId, address consumer) external;
    function getSubscription(uint256 subId)
        external
        view
        returns (uint96 balance, uint96 nativeBalance, uint64 reqCount, address owner, address[] memory consumers);
}

interface IAegisVRFConsumer {
    function setSubscriptionId(uint256 subscriptionId) external;
    function s_subscriptionId() external view returns (uint256);
}

/**
 * @title SetupVRFSubscription
 * @notice Create VRF subscription, add consumer, and configure
 *
 * Usage:
 *   forge script script/SetupVRFSubscription.s.sol:SetupVRFSubscription \
 *     --rpc-url https://sepolia.base.org \
 *     --private-key $DEPLOYER_PRIVATE_KEY \
 *     --broadcast
 *
 * After running:
 *   1. Fund the subscription with LINK at https://vrf.chain.link/base-sepolia
 *   2. Get testnet LINK from https://faucets.chain.link/base-sepolia
 */
contract SetupVRFSubscription is Script {
    // Base Sepolia addresses
    address constant VRF_COORDINATOR = 0x5C210eF41CD1a72de73bF76eC39637bB0d3d7BEE;
    address constant VRF_CONSUMER = 0x51bAC1448E5beC0E78B0408473296039A207255e;

    function run() external {
        console.log("=== AEGIS VRF Subscription Setup ===");
        console.log("");

        IVRFCoordinatorV2Plus coordinator = IVRFCoordinatorV2Plus(VRF_COORDINATOR);
        IAegisVRFConsumer consumer = IAegisVRFConsumer(VRF_CONSUMER);

        vm.startBroadcast();

        // Step 1: Create subscription
        console.log("Step 1: Creating VRF Subscription...");
        uint256 subId = coordinator.createSubscription();
        console.log("Subscription ID:", subId);

        // Step 2: Add consumer to subscription
        console.log("Step 2: Adding consumer to subscription...");
        coordinator.addConsumer(subId, VRF_CONSUMER);
        console.log("Consumer added:", VRF_CONSUMER);

        // Step 3: Update consumer's subscription ID
        console.log("Step 3: Updating consumer's subscription ID...");
        consumer.setSubscriptionId(subId);
        console.log("Consumer subscription ID set");

        vm.stopBroadcast();

        // Verify
        console.log("");
        console.log("=== Verification ===");
        (uint96 balance, uint96 nativeBalance, uint64 reqCount, address owner, address[] memory consumers) =
            coordinator.getSubscription(subId);

        console.log("Subscription ID:", subId);
        console.log("LINK Balance:", balance);
        console.log("Native Balance:", nativeBalance);
        console.log("Request Count:", reqCount);
        console.log("Owner:", owner);
        console.log("Consumer Count:", consumers.length);

        uint256 consumerSubId = consumer.s_subscriptionId();
        console.log("Consumer's Subscription ID:", consumerSubId);

        console.log("");
        console.log("=== Next Steps ===");
        console.log("1. Get testnet LINK from: https://faucets.chain.link/base-sepolia");
        console.log("2. Fund subscription at: https://vrf.chain.link/base-sepolia");
        console.log("   Subscription ID:", subId);
        console.log("3. Run: npx tsx scripts/test-vrf-request.ts");
        console.log("");
        console.log("Update .env:");
        console.log("  CHAINLINK_VRF_SUBSCRIPTION_ID=", subId);
    }
}

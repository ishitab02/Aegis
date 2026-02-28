// SPDX-License-Identifier: MIT
pragma solidity ^0.8.24;

import "forge-std/Test.sol";
import "../src/core/SentinelRegistry.sol";

contract SentinelRegistryTest is Test {
    SentinelRegistry public registry;
    address public owner;
    address public operator1;
    address public operator2;

    function setUp() public {
        owner = address(this);
        operator1 = makeAddr("operator1");
        operator2 = makeAddr("operator2");
        registry = new SentinelRegistry();
    }

    function test_RegisterSentinel() public {
        uint256 tokenId = registry.registerSentinel(
            ISentinelRegistry.SentinelType.LIQUIDITY,
            operator1,
            "ipfs://QmTestMetadata"
        );

        assertEq(tokenId, 0);
        assertEq(registry.ownerOf(0), operator1);
        assertEq(registry.tokenURI(0), "ipfs://QmTestMetadata");

        (
            ISentinelRegistry.SentinelType sentinelType,
            address op,
            bool active,
            uint256 registeredAt,
            uint256 lastActiveAt
        ) = registry.sentinels(0);

        assertEq(uint8(sentinelType), uint8(ISentinelRegistry.SentinelType.LIQUIDITY));
        assertEq(op, operator1);
        assertTrue(active);
        assertGt(registeredAt, 0);
        assertEq(registeredAt, lastActiveAt);
    }

    function test_RegisterMultipleSentinels() public {
        registry.registerSentinel(ISentinelRegistry.SentinelType.LIQUIDITY, operator1, "ipfs://1");
        registry.registerSentinel(ISentinelRegistry.SentinelType.ORACLE, operator1, "ipfs://2");
        registry.registerSentinel(ISentinelRegistry.SentinelType.GOVERNANCE, operator2, "ipfs://3");

        assertEq(registry.totalSentinels(), 3);

        uint256[] memory activeSentinels = registry.getActiveSentinels();
        assertEq(activeSentinels.length, 3);
    }

    function test_Heartbeat() public {
        registry.registerSentinel(ISentinelRegistry.SentinelType.LIQUIDITY, operator1, "ipfs://1");

        vm.warp(block.timestamp + 100);
        vm.prank(operator1);
        registry.heartbeat(0);

        (, , , , uint256 lastActiveAt) = registry.sentinels(0);
        assertEq(lastActiveAt, block.timestamp);
    }

    function test_HeartbeatRevertsIfNotOperator() public {
        registry.registerSentinel(ISentinelRegistry.SentinelType.LIQUIDITY, operator1, "ipfs://1");

        vm.prank(operator2);
        vm.expectRevert("Not operator");
        registry.heartbeat(0);
    }

    function test_Deactivate() public {
        registry.registerSentinel(ISentinelRegistry.SentinelType.LIQUIDITY, operator1, "ipfs://1");

        registry.deactivate(0);

        (, , bool active, , ) = registry.sentinels(0);
        assertFalse(active);

        uint256[] memory activeSentinels = registry.getActiveSentinels();
        assertEq(activeSentinels.length, 0);
    }

    function test_Reactivate() public {
        registry.registerSentinel(ISentinelRegistry.SentinelType.LIQUIDITY, operator1, "ipfs://1");
        registry.deactivate(0);
        registry.reactivate(0);

        (, , bool active, , ) = registry.sentinels(0);
        assertTrue(active);
    }

    function test_IsAlive() public {
        registry.registerSentinel(ISentinelRegistry.SentinelType.LIQUIDITY, operator1, "ipfs://1");

        assertTrue(registry.isAlive(0, 300));

        vm.warp(block.timestamp + 600);
        assertFalse(registry.isAlive(0, 300));

        vm.prank(operator1);
        registry.heartbeat(0);
        assertTrue(registry.isAlive(0, 300));
    }

    function test_OnlyOwnerCanRegister() public {
        vm.prank(operator1);
        vm.expectRevert(abi.encodeWithSignature("OwnableUnauthorizedAccount(address)", operator1));
        registry.registerSentinel(ISentinelRegistry.SentinelType.LIQUIDITY, operator1, "ipfs://1");
    }

    function test_GetOperatorSentinels() public {
        registry.registerSentinel(ISentinelRegistry.SentinelType.LIQUIDITY, operator1, "ipfs://1");
        registry.registerSentinel(ISentinelRegistry.SentinelType.ORACLE, operator1, "ipfs://2");

        uint256[] memory sentinels = registry.getOperatorSentinels(operator1);
        assertEq(sentinels.length, 2);
        assertEq(sentinels[0], 0);
        assertEq(sentinels[1], 1);
    }
}

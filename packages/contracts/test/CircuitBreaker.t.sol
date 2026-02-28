// SPDX-License-Identifier: MIT
pragma solidity ^0.8.24;

import "forge-std/Test.sol";
import "../src/core/CircuitBreaker.sol";
import "../src/mocks/MockProtocol.sol";

contract CircuitBreakerTest is Test {
    CircuitBreaker public breaker;
    MockProtocol public mockProtocol;
    address public admin;
    address public creWorkflow;

    function setUp() public {
        admin = address(this);
        creWorkflow = makeAddr("creWorkflow");

        breaker = new CircuitBreaker();
        mockProtocol = new MockProtocol();

        // Grant CRE workflow role
        breaker.grantRole(breaker.CRE_WORKFLOW_ROLE(), creWorkflow);

        // Register mock protocol
        breaker.registerProtocol(address(mockProtocol));
    }

    function test_RegisterProtocol() public {
        MockProtocol newProtocol = new MockProtocol();
        breaker.registerProtocol(address(newProtocol));

        assertTrue(breaker.isRegistered(address(newProtocol)));
        assertFalse(breaker.isPaused(address(newProtocol)));
    }

    function test_RegisterProtocolRevertsIfAlreadyRegistered() public {
        vm.expectRevert(
            abi.encodeWithSelector(CircuitBreaker.AlreadyRegistered.selector, address(mockProtocol))
        );
        breaker.registerProtocol(address(mockProtocol));
    }

    function test_TriggerBreaker() public {
        bytes32 threatId = keccak256("threat-1");

        vm.prank(creWorkflow);
        breaker.triggerBreaker(
            address(mockProtocol),
            threatId,
            ICircuitBreaker.ThreatLevel.CRITICAL,
            "Possible reentrancy attack"
        );

        assertTrue(breaker.isPaused(address(mockProtocol)));
        assertTrue(mockProtocol.paused());

        ICircuitBreaker.BreakerState memory state = breaker.getBreakerState(address(mockProtocol));
        assertEq(uint8(state.threatLevel), uint8(ICircuitBreaker.ThreatLevel.CRITICAL));
        assertEq(state.threatId, threatId);
    }

    function test_TriggerBreakerRevertsIfThreatLevelTooLow() public {
        bytes32 threatId = keccak256("threat-low");

        vm.prank(creWorkflow);
        vm.expectRevert(
            abi.encodeWithSelector(
                CircuitBreaker.ThreatLevelTooLow.selector, ICircuitBreaker.ThreatLevel.MEDIUM
            )
        );
        breaker.triggerBreaker(
            address(mockProtocol),
            threatId,
            ICircuitBreaker.ThreatLevel.MEDIUM,
            "Medium threat"
        );
    }

    function test_TriggerBreakerRevertsIfAlreadyPaused() public {
        bytes32 threatId = keccak256("threat-1");

        vm.prank(creWorkflow);
        breaker.triggerBreaker(
            address(mockProtocol),
            threatId,
            ICircuitBreaker.ThreatLevel.CRITICAL,
            "First trigger"
        );

        vm.prank(creWorkflow);
        vm.expectRevert(
            abi.encodeWithSelector(CircuitBreaker.AlreadyPaused.selector, address(mockProtocol))
        );
        breaker.triggerBreaker(
            address(mockProtocol),
            keccak256("threat-2"),
            ICircuitBreaker.ThreatLevel.CRITICAL,
            "Second trigger"
        );
    }

    function test_ResetBreakerAfterCooldown() public {
        bytes32 threatId = keccak256("threat-1");

        vm.prank(creWorkflow);
        breaker.triggerBreaker(
            address(mockProtocol),
            threatId,
            ICircuitBreaker.ThreatLevel.CRITICAL,
            "Attack detected"
        );

        assertTrue(breaker.isPaused(address(mockProtocol)));

        // Warp past cooldown (1 hour)
        vm.warp(block.timestamp + 1 hours + 1);

        breaker.resetBreaker(address(mockProtocol));

        assertFalse(breaker.isPaused(address(mockProtocol)));
        assertFalse(mockProtocol.paused());
    }

    function test_ResetBreakerRevertsBeforeCooldown() public {
        bytes32 threatId = keccak256("threat-1");

        vm.prank(creWorkflow);
        breaker.triggerBreaker(
            address(mockProtocol),
            threatId,
            ICircuitBreaker.ThreatLevel.CRITICAL,
            "Attack"
        );

        // Try to reset immediately
        vm.expectRevert(
            abi.encodeWithSelector(
                CircuitBreaker.CooldownNotFinished.selector, block.timestamp + 1 hours
            )
        );
        breaker.resetBreaker(address(mockProtocol));
    }

    function test_RecordAlert() public {
        bytes32 threatId = keccak256("alert-1");

        vm.prank(creWorkflow);
        breaker.recordAlert(
            address(mockProtocol), threatId, ICircuitBreaker.ThreatLevel.HIGH
        );

        assertEq(breaker.recentHighAlerts(address(mockProtocol)), 1);
        assertFalse(breaker.isPaused(address(mockProtocol)));
    }

    function test_AutoPauseAfterMultipleHighAlerts() public {
        // Send 3 HIGH alerts (autoPauseThreshold = 3)
        for (uint256 i = 0; i < 3; i++) {
            bytes32 threatId = keccak256(abi.encodePacked("alert-", i));
            vm.prank(creWorkflow);
            breaker.recordAlert(
                address(mockProtocol), threatId, ICircuitBreaker.ThreatLevel.HIGH
            );
        }

        assertTrue(breaker.isPaused(address(mockProtocol)));
        assertTrue(mockProtocol.paused());
    }

    function test_AlertCountResetsAfterTimeout() public {
        bytes32 threatId1 = keccak256("alert-1");
        vm.prank(creWorkflow);
        breaker.recordAlert(
            address(mockProtocol), threatId1, ICircuitBreaker.ThreatLevel.HIGH
        );

        assertEq(breaker.recentHighAlerts(address(mockProtocol)), 1);

        // Warp past 1 hour
        vm.warp(block.timestamp + 1 hours + 1);

        bytes32 threatId2 = keccak256("alert-2");
        vm.prank(creWorkflow);
        breaker.recordAlert(
            address(mockProtocol), threatId2, ICircuitBreaker.ThreatLevel.HIGH
        );

        // Count should have been reset, so now it's 1 again
        assertEq(breaker.recentHighAlerts(address(mockProtocol)), 1);
    }

    function test_OnlyCREWorkflowCanTrigger() public {
        bytes32 threatId = keccak256("threat-1");

        address unauthorized = makeAddr("unauthorized");
        vm.prank(unauthorized);
        vm.expectRevert();
        breaker.triggerBreaker(
            address(mockProtocol),
            threatId,
            ICircuitBreaker.ThreatLevel.CRITICAL,
            "Unauthorized"
        );
    }
}

// SPDX-License-Identifier: MIT
pragma solidity ^0.8.24;

import "forge-std/Test.sol";
import "../src/core/SentinelRegistry.sol";
import "../src/core/CircuitBreaker.sol";
import "../src/core/ThreatReport.sol";
import "../src/core/ReputationTracker.sol";
import "../src/mocks/MockProtocol.sol";

/**
 * @title IntegrationTest
 * @notice End-to-end test of the full AEGIS flow:
 *         Register sentinels → Detect threat → Trigger circuit breaker → Submit report → Update reputation
 */
contract IntegrationTest is Test {
    SentinelRegistry public registry;
    CircuitBreaker public breaker;
    ThreatReport public threatReport;
    ReputationTracker public reputation;
    MockProtocol public mockProtocol;

    address public deployer;
    address public operator;
    address public creWorkflow;

    function setUp() public {
        deployer = address(this);
        operator = makeAddr("operator");
        creWorkflow = makeAddr("creWorkflow");

        // Deploy all contracts
        registry = new SentinelRegistry();
        breaker = new CircuitBreaker();
        threatReport = new ThreatReport(creWorkflow);
        reputation = new ReputationTracker();
        mockProtocol = new MockProtocol();

        // Configure
        breaker.grantRole(breaker.CRE_WORKFLOW_ROLE(), creWorkflow);
        breaker.registerProtocol(address(mockProtocol));
        reputation.addUpdater(creWorkflow);

        // Register sentinels
        registry.registerSentinel(ISentinelRegistry.SentinelType.LIQUIDITY, operator, "ipfs://liq");
        registry.registerSentinel(ISentinelRegistry.SentinelType.ORACLE, operator, "ipfs://oracle");
        registry.registerSentinel(
            ISentinelRegistry.SentinelType.GOVERNANCE, operator, "ipfs://gov"
        );
    }

    function test_FullThreatDetectionFlow() public {
        // 1. Mock protocol has deposits
        vm.deal(address(0xBEEF), 100 ether);
        vm.prank(address(0xBEEF));
        mockProtocol.deposit{value: 100 ether}();
        assertEq(mockProtocol.getTVL(), 100 ether);

        // 2. Sentinel heartbeats (sentinels are alive)
        vm.startPrank(operator);
        registry.heartbeat(0);
        registry.heartbeat(1);
        registry.heartbeat(2);
        vm.stopPrank();

        // 3. CRE workflow detects threat and triggers circuit breaker
        bytes32 threatId = keccak256("reentrancy-attack-001");

        vm.prank(creWorkflow);
        breaker.triggerBreaker(
            address(mockProtocol),
            threatId,
            ICircuitBreaker.ThreatLevel.CRITICAL,
            "Reentrancy attack detected - TVL dropping rapidly"
        );

        // 4. Verify protocol is paused
        assertTrue(breaker.isPaused(address(mockProtocol)));
        assertTrue(mockProtocol.paused());

        // 5. Deposits should fail while paused
        vm.deal(address(0xCAFE), 10 ether);
        vm.prank(address(0xCAFE));
        vm.expectRevert(MockProtocol.ProtocolPaused.selector);
        mockProtocol.deposit{value: 10 ether}();

        // 6. Submit threat report
        IThreatReport.SentinelVote[] memory votes = new IThreatReport.SentinelVote[](3);
        votes[0] = IThreatReport.SentinelVote({
            sentinelId: 0,
            threatLevel: 4, // CRITICAL
            confidence: 9500,
            signature: hex"01"
        });
        votes[1] = IThreatReport.SentinelVote({
            sentinelId: 1,
            threatLevel: 4, // CRITICAL
            confidence: 9200,
            signature: hex"02"
        });
        votes[2] = IThreatReport.SentinelVote({
            sentinelId: 2,
            threatLevel: 3, // HIGH
            confidence: 8800,
            signature: hex"03"
        });

        bytes32 consensusHash = keccak256(abi.encode(votes));

        vm.prank(creWorkflow);
        bytes32 reportId = threatReport.submitReport(
            address(mockProtocol),
            4, // CRITICAL
            consensusHash,
            "ipfs://QmReport123",
            true,
            votes
        );

        // 7. Verify report
        (
            ,
            address protocol,
            uint8 level,
            ,
            ,
            ,
            ,
            bool action
        ) = threatReport.reports(reportId);

        assertEq(protocol, address(mockProtocol));
        assertEq(level, 4);
        assertTrue(action);

        // 8. Update sentinel reputation
        vm.startPrank(creWorkflow);
        reputation.submitFeedback(0, reportId, true, "ipfs://feedback-0");
        reputation.submitFeedback(1, reportId, true, "ipfs://feedback-1");
        reputation.submitFeedback(2, reportId, true, "ipfs://feedback-2");
        vm.stopPrank();

        // 9. Check reputation
        assertEq(reputation.getAccuracy(0), 10000); // 100%
        assertEq(reputation.getAccuracy(1), 10000);
        assertEq(reputation.getAccuracy(2), 10000);

        // 10. Reset circuit breaker after cooldown
        vm.warp(block.timestamp + 1 hours + 1);
        breaker.resetBreaker(address(mockProtocol));
        assertFalse(breaker.isPaused(address(mockProtocol)));

        // 11. Protocol should be operational again
        vm.prank(address(0xCAFE));
        mockProtocol.deposit{value: 10 ether}();
        assertEq(mockProtocol.getTVL(), 110 ether);
    }
}

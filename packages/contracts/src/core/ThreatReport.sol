// SPDX-License-Identifier: MIT
pragma solidity ^0.8.24;

import "../interfaces/IThreatReport.sol";

/**
 * @title ThreatReport
 * @notice Immutable storage for AEGIS threat reports
 * @dev Reports are submitted by CRE workflows with consensus verification
 */
contract ThreatReport is IThreatReport {
    // ============ State Variables ============

    mapping(bytes32 => Report) public reports;
    mapping(bytes32 => SentinelVote[]) internal _reportVotes;
    mapping(address => bytes32[]) public protocolReports;
    bytes32[] public allReports;

    address public creWorkflow;
    address public owner;

    // ============ Errors ============

    error OnlyCREWorkflow();
    error ReportAlreadyExists(bytes32 reportId);

    // ============ Modifiers ============

    modifier onlyCRE() {
        if (msg.sender != creWorkflow) revert OnlyCREWorkflow();
        _;
    }

    // ============ Constructor ============

    constructor(address _creWorkflow) {
        creWorkflow = _creWorkflow;
        owner = msg.sender;
    }

    // ============ External Functions ============

    /// @inheritdoc IThreatReport
    function submitReport(
        address protocol,
        uint8 threatLevel,
        bytes32 consensusHash,
        string calldata ipfsHash,
        bool actionTaken,
        SentinelVote[] calldata votes
    ) external onlyCRE returns (bytes32 reportId) {
        reportId = keccak256(abi.encodePacked(protocol, block.timestamp, block.number, consensusHash));

        if (reports[reportId].timestamp != 0) revert ReportAlreadyExists(reportId);

        reports[reportId] = Report({
            reportId: reportId,
            protocol: protocol,
            threatLevel: threatLevel,
            timestamp: block.timestamp,
            blockNumber: block.number,
            consensusHash: consensusHash,
            ipfsHash: ipfsHash,
            actionTaken: actionTaken
        });

        for (uint256 i = 0; i < votes.length; i++) {
            _reportVotes[reportId].push(votes[i]);
        }

        protocolReports[protocol].push(reportId);
        allReports.push(reportId);

        emit ReportSubmitted(reportId, protocol, threatLevel, actionTaken);
    }

    /// @inheritdoc IThreatReport
    function getProtocolReports(address protocol, uint256 limit)
        external
        view
        returns (bytes32[] memory)
    {
        bytes32[] storage all = protocolReports[protocol];
        uint256 count = limit < all.length ? limit : all.length;

        bytes32[] memory result = new bytes32[](count);
        for (uint256 i = 0; i < count; i++) {
            result[i] = all[all.length - 1 - i]; // Most recent first
        }

        return result;
    }

    /// @inheritdoc IThreatReport
    function getReportVotes(bytes32 reportId) external view returns (SentinelVote[] memory) {
        return _reportVotes[reportId];
    }

    /**
     * @notice Get total number of reports
     */
    function totalReports() external view returns (uint256) {
        return allReports.length;
    }

    /**
     * @notice Update the CRE workflow address
     * @param newWorkflow New authorized workflow address
     */
    function setCREWorkflow(address newWorkflow) external {
        require(msg.sender == owner, "Only owner");
        creWorkflow = newWorkflow;
    }
}

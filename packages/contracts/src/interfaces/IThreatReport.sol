// SPDX-License-Identifier: MIT
pragma solidity ^0.8.24;

interface IThreatReport {
    struct Report {
        bytes32 reportId;
        address protocol;
        uint8 threatLevel;
        uint256 timestamp;
        uint256 blockNumber;
        bytes32 consensusHash;
        string ipfsHash;
        bool actionTaken;
    }

    struct SentinelVote {
        uint256 sentinelId;
        uint8 threatLevel;
        uint256 confidence;
        bytes signature;
    }

    event ReportSubmitted(
        bytes32 indexed reportId,
        address indexed protocol,
        uint8 threatLevel,
        bool actionTaken
    );

    function submitReport(
        address protocol,
        uint8 threatLevel,
        bytes32 consensusHash,
        string calldata ipfsHash,
        bool actionTaken,
        SentinelVote[] calldata votes
    ) external returns (bytes32 reportId);

    function getProtocolReports(address protocol, uint256 limit)
        external
        view
        returns (bytes32[] memory);

    function getReportVotes(bytes32 reportId) external view returns (SentinelVote[] memory);
}

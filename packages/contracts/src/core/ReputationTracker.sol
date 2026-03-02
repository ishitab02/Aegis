// SPDX-License-Identifier: MIT
pragma solidity ^0.8.24;

/**
 * @title ReputationTracker
 * @notice ERC-8004 compatible reputation tracking for AEGIS sentinels
 */
contract ReputationTracker {
    struct ReputationScore {
        uint256 totalPredictions;
        uint256 correctPredictions;
        uint256 falsePositives;
        uint256 missedThreats;
        uint256 lastUpdated;
    }

    struct FeedbackEntry {
        uint256 sentinelId;
        bytes32 reportId;
        bool wasCorrect;
        string feedbackUri;
        uint256 timestamp;
    }

    mapping(uint256 => ReputationScore) public reputations;
    mapping(uint256 => FeedbackEntry[]) internal _feedbackHistory;
    mapping(address => bool) public authorizedUpdaters;

    address public owner;

    event ReputationUpdated(uint256 indexed sentinelId, bool wasCorrect, uint256 newAccuracy);
    event FeedbackSubmitted(uint256 indexed sentinelId, bytes32 indexed reportId, bool wasCorrect);

    error NotAuthorized();
    error OnlyOwner();

    constructor() {
        owner = msg.sender;
        authorizedUpdaters[msg.sender] = true;
    }

    function submitFeedback(uint256 sentinelId, bytes32 reportId, bool wasCorrect, string calldata feedbackUri)
        external
    {
        if (!authorizedUpdaters[msg.sender]) revert NotAuthorized();

        ReputationScore storage rep = reputations[sentinelId];

        rep.totalPredictions++;
        if (wasCorrect) {
            rep.correctPredictions++;
        } else {
            rep.falsePositives++;
        }
        rep.lastUpdated = block.timestamp;

        _feedbackHistory[sentinelId].push(
            FeedbackEntry({
                sentinelId: sentinelId,
                reportId: reportId,
                wasCorrect: wasCorrect,
                feedbackUri: feedbackUri,
                timestamp: block.timestamp
            })
        );

        emit FeedbackSubmitted(sentinelId, reportId, wasCorrect);
        emit ReputationUpdated(sentinelId, wasCorrect, getAccuracy(sentinelId));
    }

    /// @dev sentinel failed to detect an actual threat
    function recordMissedThreat(uint256 sentinelId) external {
        if (!authorizedUpdaters[msg.sender]) revert NotAuthorized();

        reputations[sentinelId].missedThreats++;
        reputations[sentinelId].lastUpdated = block.timestamp;
    }

    /// @return accuracy in basis points (9500 = 95%)
    function getAccuracy(uint256 sentinelId) public view returns (uint256) {
        ReputationScore memory rep = reputations[sentinelId];

        if (rep.totalPredictions == 0) {
            return 10000; // 100% if no predictions yet
        }

        return (rep.correctPredictions * 10000) / rep.totalPredictions;
    }

    /// @dev unlike accuracy, accounts for missed threats
    /// @return reliability in basis points
    function getReliability(uint256 sentinelId) public view returns (uint256) {
        ReputationScore memory rep = reputations[sentinelId];

        uint256 totalOpportunities = rep.totalPredictions + rep.missedThreats;
        if (totalOpportunities == 0) {
            return 10000;
        }

        return (rep.correctPredictions * 10000) / totalOpportunities;
    }

    function getFeedbackHistory(uint256 sentinelId) external view returns (FeedbackEntry[] memory) {
        return _feedbackHistory[sentinelId];
    }

    function addUpdater(address updater) external {
        if (msg.sender != owner) revert OnlyOwner();
        authorizedUpdaters[updater] = true;
    }

    function removeUpdater(address updater) external {
        if (msg.sender != owner) revert OnlyOwner();
        authorizedUpdaters[updater] = false;
    }
}

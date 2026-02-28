// SPDX-License-Identifier: MIT
pragma solidity ^0.8.24;

/**
 * @title ReputationTracker
 * @notice ERC-8004 compatible reputation tracking for AEGIS sentinels
 * @dev Tracks accuracy and reliability of sentinel predictions over time
 */
contract ReputationTracker {
    // ============ Structs ============

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

    // ============ State Variables ============

    mapping(uint256 => ReputationScore) public reputations;
    mapping(uint256 => FeedbackEntry[]) internal _feedbackHistory;
    mapping(address => bool) public authorizedUpdaters;

    address public owner;

    // ============ Events ============

    event ReputationUpdated(uint256 indexed sentinelId, bool wasCorrect, uint256 newAccuracy);
    event FeedbackSubmitted(uint256 indexed sentinelId, bytes32 indexed reportId, bool wasCorrect);

    // ============ Errors ============

    error NotAuthorized();
    error OnlyOwner();

    // ============ Constructor ============

    constructor() {
        owner = msg.sender;
        authorizedUpdaters[msg.sender] = true;
    }

    // ============ External Functions ============

    /**
     * @notice Submit feedback for a sentinel's prediction
     * @param sentinelId The sentinel's token ID
     * @param reportId The report this feedback is for
     * @param wasCorrect Whether the prediction was correct
     * @param feedbackUri IPFS URI to detailed feedback
     */
    function submitFeedback(
        uint256 sentinelId,
        bytes32 reportId,
        bool wasCorrect,
        string calldata feedbackUri
    ) external {
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

    /**
     * @notice Record a missed threat (sentinel didn't detect it)
     * @param sentinelId The sentinel's token ID
     */
    function recordMissedThreat(uint256 sentinelId) external {
        if (!authorizedUpdaters[msg.sender]) revert NotAuthorized();

        reputations[sentinelId].missedThreats++;
        reputations[sentinelId].lastUpdated = block.timestamp;
    }

    /**
     * @notice Get accuracy percentage for a sentinel
     * @param sentinelId The sentinel's token ID
     * @return Accuracy in basis points (9500 = 95%)
     */
    function getAccuracy(uint256 sentinelId) public view returns (uint256) {
        ReputationScore memory rep = reputations[sentinelId];

        if (rep.totalPredictions == 0) {
            return 10000; // 100% if no predictions yet
        }

        return (rep.correctPredictions * 10000) / rep.totalPredictions;
    }

    /**
     * @notice Get reliability score (accounts for missed threats)
     * @param sentinelId The sentinel's token ID
     * @return Reliability in basis points
     */
    function getReliability(uint256 sentinelId) public view returns (uint256) {
        ReputationScore memory rep = reputations[sentinelId];

        uint256 totalOpportunities = rep.totalPredictions + rep.missedThreats;
        if (totalOpportunities == 0) {
            return 10000;
        }

        return (rep.correctPredictions * 10000) / totalOpportunities;
    }

    /**
     * @notice Get feedback history for a sentinel
     * @param sentinelId The sentinel's token ID
     */
    function getFeedbackHistory(uint256 sentinelId) external view returns (FeedbackEntry[] memory) {
        return _feedbackHistory[sentinelId];
    }

    /**
     * @notice Add an authorized updater
     */
    function addUpdater(address updater) external {
        if (msg.sender != owner) revert OnlyOwner();
        authorizedUpdaters[updater] = true;
    }

    /**
     * @notice Remove an authorized updater
     */
    function removeUpdater(address updater) external {
        if (msg.sender != owner) revert OnlyOwner();
        authorizedUpdaters[updater] = false;
    }
}

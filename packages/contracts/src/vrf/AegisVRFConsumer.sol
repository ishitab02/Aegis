// SPDX-License-Identifier: MIT
pragma solidity ^0.8.24;

import {VRFConsumerBaseV2Plus} from "@chainlink/contracts/src/v0.8/vrf/dev/VRFConsumerBaseV2Plus.sol";
import {VRFV2PlusClient} from "@chainlink/contracts/src/v0.8/vrf/dev/libraries/VRFV2PlusClient.sol";

/**
 * @title AegisVRFConsumer
 * @notice VRF v2.5 consumer for AEGIS Protocol tie-breaker selection
 * @dev Used when sentinels have a split vote (1-1) to fairly select the deciding sentinel
 *
 * Base Sepolia Configuration:
 * - VRF Coordinator: 0x5C210eF41CD1a72de73bF76eC39637bB0d3d7BEE
 * - LINK Token: 0xE4aB69C077896252FAFBD49EFD26B5D171A32410
 * - Key Hash (500 gwei): 0x9e9e46732b32662b9adc6f3abdf6c5e926a666d174a4d6b8e39c4cca76a38897
 */
contract AegisVRFConsumer is VRFConsumerBaseV2Plus {
    // ============ Events ============

    event RandomnessRequested(uint256 indexed requestId, uint256 indexed tieBreakerId, uint256[] sentinelIds);

    event RandomnessFulfilled(
        uint256 indexed requestId, uint256 indexed tieBreakerId, uint256 selectedSentinelId, uint256 randomWord
    );

    // ============ Errors ============

    error RequestNotFound(uint256 requestId);
    error InvalidSentinelCount();
    error NotAuthorized();

    // ============ State Variables ============

    /// @notice VRF configuration
    bytes32 public immutable i_keyHash;
    uint256 public s_subscriptionId;
    uint32 public s_callbackGasLimit;
    uint16 public s_requestConfirmations;

    /// @notice Counter for tie-breaker IDs
    uint256 public s_tieBreakCounter;

    /// @notice Request tracking
    struct TieBreakRequest {
        uint256 tieBreakerId;
        uint256[] sentinelIds;
        uint256 selectedSentinelId;
        uint256 randomWord;
        bool fulfilled;
    }

    /// @notice requestId => TieBreakRequest
    mapping(uint256 => TieBreakRequest) public s_requests;

    /// @notice tieBreakerId => requestId (for lookup)
    mapping(uint256 => uint256) public s_tieBreakToRequest;

    /// @notice Last completed tie-break result
    uint256 public s_lastSelectedSentinel;
    uint256 public s_lastRandomWord;
    uint256 public s_lastRequestId;

    // ============ Constructor ============

    /**
     * @param vrfCoordinator VRF Coordinator address
     * @param keyHash The key hash for the VRF job
     * @param subscriptionId The subscription ID for VRF
     * @param callbackGasLimit Gas limit for the callback
     * @param requestConfirmations Number of confirmations required
     */
    constructor(
        address vrfCoordinator,
        bytes32 keyHash,
        uint256 subscriptionId,
        uint32 callbackGasLimit,
        uint16 requestConfirmations
    ) VRFConsumerBaseV2Plus(vrfCoordinator) {
        i_keyHash = keyHash;
        s_subscriptionId = subscriptionId;
        s_callbackGasLimit = callbackGasLimit;
        s_requestConfirmations = requestConfirmations;
    }

    // ============ External Functions ============

    /**
     * @notice Request randomness for a tie-breaker selection
     * @param sentinelIds Array of sentinel IDs to choose from (must be 2+)
     * @return requestId The VRF request ID
     * @return tieBreakerId The AEGIS tie-breaker ID
     */
    function requestTieBreaker(uint256[] calldata sentinelIds)
        external
        onlyOwner
        returns (uint256 requestId, uint256 tieBreakerId)
    {
        if (sentinelIds.length < 2) revert InvalidSentinelCount();

        tieBreakerId = ++s_tieBreakCounter;

        // Request randomness using VRF v2.5
        requestId = s_vrfCoordinator.requestRandomWords(
            VRFV2PlusClient.RandomWordsRequest({
                keyHash: i_keyHash,
                subId: s_subscriptionId,
                requestConfirmations: s_requestConfirmations,
                callbackGasLimit: s_callbackGasLimit,
                numWords: 1,
                extraArgs: VRFV2PlusClient._argsToBytes(VRFV2PlusClient.ExtraArgsV1({nativePayment: false}))
            })
        );

        // Store the request
        s_requests[requestId] = TieBreakRequest({
            tieBreakerId: tieBreakerId, sentinelIds: sentinelIds, selectedSentinelId: 0, randomWord: 0, fulfilled: false
        });

        s_tieBreakToRequest[tieBreakerId] = requestId;
        s_lastRequestId = requestId;

        emit RandomnessRequested(requestId, tieBreakerId, sentinelIds);
    }

    /**
     * @notice Update subscription ID
     * @param subscriptionId New subscription ID
     */
    function setSubscriptionId(uint256 subscriptionId) external onlyOwner {
        s_subscriptionId = subscriptionId;
    }

    /**
     * @notice Update callback gas limit
     * @param callbackGasLimit New callback gas limit
     */
    function setCallbackGasLimit(uint32 callbackGasLimit) external onlyOwner {
        s_callbackGasLimit = callbackGasLimit;
    }

    /**
     * @notice Update request confirmations
     * @param requestConfirmations New confirmation count
     */
    function setRequestConfirmations(uint16 requestConfirmations) external onlyOwner {
        s_requestConfirmations = requestConfirmations;
    }

    // ============ View Functions ============

    /**
     * @notice Get tie-break result by request ID
     * @param requestId The VRF request ID
     * @return The tie-break request data
     */
    function getRequest(uint256 requestId) external view returns (TieBreakRequest memory) {
        return s_requests[requestId];
    }

    /**
     * @notice Get tie-break result by tie-breaker ID
     * @param tieBreakerId The AEGIS tie-breaker ID
     * @return The tie-break request data
     */
    function getTieBreakResult(uint256 tieBreakerId) external view returns (TieBreakRequest memory) {
        uint256 requestId = s_tieBreakToRequest[tieBreakerId];
        return s_requests[requestId];
    }

    /**
     * @notice Check if a request has been fulfilled
     * @param requestId The VRF request ID
     * @return True if fulfilled
     */
    function isRequestFulfilled(uint256 requestId) external view returns (bool) {
        return s_requests[requestId].fulfilled;
    }

    /**
     * @notice Get the last selected sentinel from the most recent tie-break
     * @return The sentinel ID that was selected
     */
    function getLastSelectedSentinel() external view returns (uint256) {
        return s_lastSelectedSentinel;
    }

    // ============ Internal Functions ============

    /**
     * @notice Callback function used by VRF Coordinator
     * @param requestId The VRF request ID
     * @param randomWords Array of random words (we use 1)
     */
    function fulfillRandomWords(uint256 requestId, uint256[] calldata randomWords) internal override {
        TieBreakRequest storage request = s_requests[requestId];

        if (request.sentinelIds.length == 0) revert RequestNotFound(requestId);

        uint256 randomWord = randomWords[0];
        uint256 selectedIndex = randomWord % request.sentinelIds.length;
        uint256 selectedSentinelId = request.sentinelIds[selectedIndex];

        // Store results
        request.randomWord = randomWord;
        request.selectedSentinelId = selectedSentinelId;
        request.fulfilled = true;

        // Update last result for easy access
        s_lastSelectedSentinel = selectedSentinelId;
        s_lastRandomWord = randomWord;

        emit RandomnessFulfilled(requestId, request.tieBreakerId, selectedSentinelId, randomWord);
    }
}

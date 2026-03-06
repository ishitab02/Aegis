// SPDX-License-Identifier: MIT
pragma solidity ^0.8.24;

/**
 * @title AlertReceiver
 * @notice Receives AEGIS threat alerts from other chains via Chainlink CCIP.
 * @dev Implements the CCIP receiver interface without inheriting from the Chainlink
 *      library (to keep dependencies minimal).  Deploy this on Arbitrum Sepolia
 *      and use its address as the --receiver flag in test-ccip-alert.ts.
 *
 * CCIP Router (Arbitrum Sepolia): 0x2a9C5afB0d0e4BAb2BCdaE109EC4b0c4Be15a165
 */
contract AlertReceiver {

    // ============ CCIP Structs (mirrored from Client.sol) ============

    struct EVMTokenAmount {
        address token;
        uint256 amount;
    }

    struct Any2EVMMessage {
        bytes32 messageId;          // unique CCIP message ID
        uint64  sourceChainSelector; // source chain (e.g. Base Sepolia)
        bytes   sender;              // ABI-encoded sender address
        bytes   data;                // arbitrary payload
        EVMTokenAmount[] destTokenAmounts;
    }

    // ============ State ============

    address public immutable ccipRouter;
    address public owner;

    struct Alert {
        bytes32 messageId;
        uint64  sourceChainSelector;
        address senderAddress;
        string  alertType;
        address protocol;
        bytes32 threatId;
        uint8   threatLevel;
        uint256 alertTimestamp;
        string  description;
        uint256 receivedAt;
    }

    mapping(bytes32 => Alert) public alerts;
    bytes32[] public alertIds;

    // ============ Events ============

    event AlertReceived(
        bytes32 indexed messageId,
        uint64  indexed sourceChainSelector,
        address indexed senderAddress,
        string  alertType,
        address protocol,
        uint8   threatLevel,
        string  description
    );

    event CCIPRouterUpdated(address oldRouter, address newRouter);

    // ============ Errors ============

    error OnlyCCIPRouter(address caller, address router);
    error OnlyOwner(address caller);
    error AlertAlreadyProcessed(bytes32 messageId);

    // ============ Constructor ============

    /**
     * @param _ccipRouter CCIP Router address on this chain.
     *   Arbitrum Sepolia: 0x2a9C5afB0d0e4BAb2BCdaE109EC4b0c4Be15a165
     */
    constructor(address _ccipRouter) {
        ccipRouter = _ccipRouter;
        owner = msg.sender;
    }

    // ============ CCIP Receive ============

    /**
     * @notice Called by the CCIP Router when a cross-chain message arrives.
     * @dev Only the CCIP Router is allowed to call this function.
     */
    function ccipReceive(Any2EVMMessage calldata message) external {
        if (msg.sender != ccipRouter) revert OnlyCCIPRouter(msg.sender, ccipRouter);
        if (alerts[message.messageId].receivedAt != 0) revert AlertAlreadyProcessed(message.messageId);

        // Decode AEGIS alert payload
        // Matches the encoding in scripts/test-ccip-alert.ts:
        //   abi.encode(string alertType, address protocol, bytes32 threatId,
        //              uint8 threatLevel, uint256 timestamp, string description)
        (
            string  memory alertType,
            address         protocol,
            bytes32         threatId,
            uint8           threatLevel,
            uint256         alertTimestamp,
            string  memory  description
        ) = abi.decode(message.data, (string, address, bytes32, uint8, uint256, string));

        // Recover sender address (ABI-encoded as 32 bytes)
        address senderAddress = abi.decode(message.sender, (address));

        // Store alert
        alerts[message.messageId] = Alert({
            messageId:           message.messageId,
            sourceChainSelector: message.sourceChainSelector,
            senderAddress:       senderAddress,
            alertType:           alertType,
            protocol:            protocol,
            threatId:            threatId,
            threatLevel:         threatLevel,
            alertTimestamp:      alertTimestamp,
            description:         description,
            receivedAt:          block.timestamp
        });
        alertIds.push(message.messageId);

        emit AlertReceived(
            message.messageId,
            message.sourceChainSelector,
            senderAddress,
            alertType,
            protocol,
            threatLevel,
            description
        );
    }

    // ============ Views ============

    function getAlertCount() external view returns (uint256) {
        return alertIds.length;
    }

    function getLatestAlert() external view returns (Alert memory) {
        require(alertIds.length > 0, "No alerts received yet");
        return alerts[alertIds[alertIds.length - 1]];
    }

    function getAllAlerts() external view returns (Alert[] memory) {
        Alert[] memory result = new Alert[](alertIds.length);
        for (uint256 i = 0; i < alertIds.length; i++) {
            result[i] = alerts[alertIds[i]];
        }
        return result;
    }

    /**
     * @notice ERC-165 support: indicates this contract can receive CCIP messages.
     */
    function supportsInterface(bytes4 interfaceId) external pure returns (bool) {
        // IAny2EVMMessageReceiver interface ID: 0x85572ffb
        return interfaceId == 0x85572ffb || interfaceId == 0x01ffc9a7;
    }

    // ============ Admin ============

    modifier onlyOwner() {
        if (msg.sender != owner) revert OnlyOwner(msg.sender);
        _;
    }

    function transferOwnership(address newOwner) external onlyOwner {
        owner = newOwner;
    }
}

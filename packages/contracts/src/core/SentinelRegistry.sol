// SPDX-License-Identifier: MIT
pragma solidity ^0.8.24;

import "@openzeppelin/contracts/token/ERC721/extensions/ERC721URIStorage.sol";
import "@openzeppelin/contracts/access/Ownable.sol";
import "../interfaces/ISentinelRegistry.sol";

/**
 * @title SentinelRegistry
 * @notice Registry for AEGIS sentinel agents, ERC-8004 compatible
 * @dev Each sentinel is represented as an NFT with metadata URI
 */
contract SentinelRegistry is ISentinelRegistry, ERC721URIStorage, Ownable {
    // ============ State Variables ============

    uint256 private _nextTokenId;

    mapping(uint256 => Sentinel) public sentinels;
    mapping(address => uint256[]) public operatorSentinels;

    // ============ Constructor ============

    constructor() ERC721("AEGIS Sentinel", "AEGIS") Ownable(msg.sender) {}

    // ============ External Functions ============

    /// @inheritdoc ISentinelRegistry
    function registerSentinel(
        SentinelType sentinelType,
        address operator,
        string calldata metadataUri
    ) external onlyOwner returns (uint256 tokenId) {
        tokenId = _nextTokenId++;

        _mint(operator, tokenId);
        _setTokenURI(tokenId, metadataUri);

        sentinels[tokenId] = Sentinel({
            sentinelType: sentinelType,
            operator: operator,
            active: true,
            registeredAt: block.timestamp,
            lastActiveAt: block.timestamp
        });

        operatorSentinels[operator].push(tokenId);

        emit SentinelRegistered(tokenId, sentinelType, operator, metadataUri);
    }

    /// @inheritdoc ISentinelRegistry
    function heartbeat(uint256 tokenId) external {
        require(sentinels[tokenId].operator == msg.sender, "Not operator");
        require(sentinels[tokenId].active, "Sentinel not active");

        sentinels[tokenId].lastActiveAt = block.timestamp;

        emit SentinelHeartbeat(tokenId, block.timestamp);
    }

    /// @inheritdoc ISentinelRegistry
    function deactivate(uint256 tokenId) external onlyOwner {
        require(sentinels[tokenId].active, "Already inactive");
        sentinels[tokenId].active = false;
        emit SentinelDeactivated(tokenId);
    }

    /**
     * @notice Reactivate a previously deactivated sentinel
     * @param tokenId The sentinel's token ID
     */
    function reactivate(uint256 tokenId) external onlyOwner {
        require(!sentinels[tokenId].active, "Already active");
        sentinels[tokenId].active = true;
        sentinels[tokenId].lastActiveAt = block.timestamp;
        emit SentinelReactivated(tokenId);
    }

    /// @inheritdoc ISentinelRegistry
    function getActiveSentinels() external view returns (uint256[] memory) {
        uint256 activeCount = 0;
        for (uint256 i = 0; i < _nextTokenId; i++) {
            if (sentinels[i].active) activeCount++;
        }

        uint256[] memory active = new uint256[](activeCount);
        uint256 index = 0;
        for (uint256 i = 0; i < _nextTokenId; i++) {
            if (sentinels[i].active) {
                active[index++] = i;
            }
        }

        return active;
    }

    /// @inheritdoc ISentinelRegistry
    function isAlive(uint256 tokenId, uint256 maxInactivity) external view returns (bool) {
        Sentinel memory s = sentinels[tokenId];
        return s.active && (block.timestamp - s.lastActiveAt <= maxInactivity);
    }

    /**
     * @notice Get all sentinel IDs for an operator
     * @param operator The operator address
     */
    function getOperatorSentinels(address operator) external view returns (uint256[] memory) {
        return operatorSentinels[operator];
    }

    /**
     * @notice Get total number of registered sentinels
     */
    function totalSentinels() external view returns (uint256) {
        return _nextTokenId;
    }
}

// SPDX-License-Identifier: MIT
pragma solidity ^0.8.24;

interface ISentinelRegistry {
    enum SentinelType {
        LIQUIDITY,
        ORACLE,
        GOVERNANCE,
        SHERLOCK
    }

    struct Sentinel {
        SentinelType sentinelType;
        address operator;
        bool active;
        uint256 registeredAt;
        uint256 lastActiveAt;
    }

    event SentinelRegistered(
        uint256 indexed tokenId,
        SentinelType sentinelType,
        address indexed operator,
        string metadataUri
    );
    event SentinelDeactivated(uint256 indexed tokenId);
    event SentinelReactivated(uint256 indexed tokenId);
    event SentinelHeartbeat(uint256 indexed tokenId, uint256 timestamp);

    function registerSentinel(
        SentinelType sentinelType,
        address operator,
        string calldata metadataUri
    ) external returns (uint256 tokenId);

    function heartbeat(uint256 tokenId) external;

    function deactivate(uint256 tokenId) external;

    function getActiveSentinels() external view returns (uint256[] memory);

    function isAlive(uint256 tokenId, uint256 maxInactivity) external view returns (bool);
}

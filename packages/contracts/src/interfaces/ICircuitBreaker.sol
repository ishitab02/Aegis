// SPDX-License-Identifier: MIT
pragma solidity ^0.8.24;

interface ICircuitBreaker {
    enum ThreatLevel {
        NONE,
        LOW,
        MEDIUM,
        HIGH,
        CRITICAL
    }

    struct BreakerState {
        bool paused;
        ThreatLevel threatLevel;
        bytes32 threatId;
        uint256 pausedAt;
        uint256 cooldownEnds;
        string reason;
    }

    event ProtocolRegistered(address indexed protocol);
    event CircuitBreakerTriggered(
        address indexed protocol,
        bytes32 indexed threatId,
        ThreatLevel threatLevel,
        string reason
    );
    event CircuitBreakerReset(address indexed protocol, address indexed resetBy);
    event ThreatAlertRecorded(address indexed protocol, bytes32 indexed threatId, ThreatLevel threatLevel);

    function registerProtocol(address protocol) external;

    function triggerBreaker(
        address protocol,
        bytes32 threatId,
        ThreatLevel threatLevel,
        string calldata reason
    ) external;

    function recordAlert(address protocol, bytes32 threatId, ThreatLevel threatLevel) external;

    function resetBreaker(address protocol) external;

    function isPaused(address protocol) external view returns (bool);

    function getBreakerState(address protocol) external view returns (BreakerState memory);
}

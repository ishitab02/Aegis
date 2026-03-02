// SPDX-License-Identifier: MIT
pragma solidity ^0.8.24;

import "@openzeppelin/contracts/access/AccessControl.sol";
import "@openzeppelin/contracts/utils/ReentrancyGuard.sol";
import "../interfaces/ICircuitBreaker.sol";

/**
 * @title CircuitBreaker
 * @notice emergency pause controller for DeFi protocols
 * @dev can be triggered by CRE workflows with consensus verification
 */
contract CircuitBreaker is ICircuitBreaker, AccessControl, ReentrancyGuard {
    bytes32 public constant PAUSER_ROLE = keccak256("PAUSER_ROLE");
    bytes32 public constant UNPAUSER_ROLE = keccak256("UNPAUSER_ROLE");
    bytes32 public constant CRE_WORKFLOW_ROLE = keccak256("CRE_WORKFLOW_ROLE");

    mapping(address => BreakerState) public protocolStates;
    address[] public registeredProtocols;
    mapping(address => bool) public isRegistered;

    uint256 public cooldownPeriod = 1 hours;
    uint256 public autoPauseThreshold = 3;

    mapping(address => uint256) public recentHighAlerts;
    mapping(address => uint256) public lastAlertTimestamp;

    error AlreadyRegistered(address protocol);
    error NotRegistered(address protocol);
    error AlreadyPaused(address protocol);
    error NotPaused(address protocol);
    error ThreatLevelTooLow(ThreatLevel provided);
    error CooldownNotFinished(uint256 cooldownEnds);

    constructor() {
        _grantRole(DEFAULT_ADMIN_ROLE, msg.sender);
        _grantRole(PAUSER_ROLE, msg.sender);
        _grantRole(UNPAUSER_ROLE, msg.sender);
    }

    /// @inheritdoc ICircuitBreaker
    function registerProtocol(address protocol) external onlyRole(DEFAULT_ADMIN_ROLE) {
        if (isRegistered[protocol]) revert AlreadyRegistered(protocol);

        registeredProtocols.push(protocol);
        isRegistered[protocol] = true;

        protocolStates[protocol] = BreakerState({
            paused: false, threatLevel: ThreatLevel.NONE, threatId: bytes32(0), pausedAt: 0, cooldownEnds: 0, reason: ""
        });

        emit ProtocolRegistered(protocol);
    }

    /// @inheritdoc ICircuitBreaker
    function triggerBreaker(address protocol, bytes32 threatId, ThreatLevel threatLevel, string calldata reason)
        external
        onlyRole(CRE_WORKFLOW_ROLE)
        nonReentrant
    {
        if (!isRegistered[protocol]) revert NotRegistered(protocol);
        if (protocolStates[protocol].paused) revert AlreadyPaused(protocol);
        if (threatLevel < ThreatLevel.HIGH) revert ThreatLevelTooLow(threatLevel);

        protocolStates[protocol] = BreakerState({
            paused: true,
            threatLevel: threatLevel,
            threatId: threatId,
            pausedAt: block.timestamp,
            cooldownEnds: block.timestamp + cooldownPeriod,
            reason: reason
        });

        _attemptProtocolPause(protocol);

        emit CircuitBreakerTriggered(protocol, threatId, threatLevel, reason);
    }

    /// @inheritdoc ICircuitBreaker
    function recordAlert(address protocol, bytes32 threatId, ThreatLevel threatLevel)
        external
        onlyRole(CRE_WORKFLOW_ROLE)
    {
        if (!isRegistered[protocol]) revert NotRegistered(protocol);

        // Reset alert count if last alert was > 1 hour ago
        if (block.timestamp - lastAlertTimestamp[protocol] > 1 hours) {
            recentHighAlerts[protocol] = 0;
        }

        if (threatLevel >= ThreatLevel.HIGH) {
            recentHighAlerts[protocol]++;
            lastAlertTimestamp[protocol] = block.timestamp;

            if (recentHighAlerts[protocol] >= autoPauseThreshold) {
                _autoPause(protocol, threatId);
            }
        }

        emit ThreatAlertRecorded(protocol, threatId, threatLevel);
    }

    /// @inheritdoc ICircuitBreaker
    function resetBreaker(address protocol) external onlyRole(UNPAUSER_ROLE) {
        if (!protocolStates[protocol].paused) revert NotPaused(protocol);
        if (block.timestamp < protocolStates[protocol].cooldownEnds) {
            revert CooldownNotFinished(protocolStates[protocol].cooldownEnds);
        }

        protocolStates[protocol].paused = false;
        protocolStates[protocol].threatLevel = ThreatLevel.NONE;
        recentHighAlerts[protocol] = 0;

        _attemptProtocolUnpause(protocol);

        emit CircuitBreakerReset(protocol, msg.sender);
    }

    /// @inheritdoc ICircuitBreaker
    function isPaused(address protocol) external view returns (bool) {
        return protocolStates[protocol].paused;
    }

    /// @inheritdoc ICircuitBreaker
    function getBreakerState(address protocol) external view returns (BreakerState memory) {
        return protocolStates[protocol];
    }

    function getRegisteredProtocols() external view returns (address[] memory) {
        return registeredProtocols;
    }

    function setCooldownPeriod(uint256 newCooldown) external onlyRole(DEFAULT_ADMIN_ROLE) {
        cooldownPeriod = newCooldown;
    }

    /// @param newThreshold number of HIGH alerts before auto-pause
    function setAutoPauseThreshold(uint256 newThreshold) external onlyRole(DEFAULT_ADMIN_ROLE) {
        autoPauseThreshold = newThreshold;
    }

    function _autoPause(address protocol, bytes32 threatId) internal {
        if (!protocolStates[protocol].paused) {
            protocolStates[protocol] = BreakerState({
                paused: true,
                threatLevel: ThreatLevel.HIGH,
                threatId: threatId,
                pausedAt: block.timestamp,
                cooldownEnds: block.timestamp + cooldownPeriod,
                reason: "Auto-paused: multiple HIGH alerts"
            });

            _attemptProtocolPause(protocol);

            emit CircuitBreakerTriggered(protocol, threatId, ThreatLevel.HIGH, "Auto-paused: multiple HIGH alerts");
        }
    }

    function _attemptProtocolPause(address protocol) internal {
        // Best-effort call - protocol must grant us permission
        (bool success,) = protocol.call(abi.encodeWithSignature("pause()"));
        // Silence unused variable warning
        success;
    }

    function _attemptProtocolUnpause(address protocol) internal {
        (bool success,) = protocol.call(abi.encodeWithSignature("unpause()"));
        success;
    }
}

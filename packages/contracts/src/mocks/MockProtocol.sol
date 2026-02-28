// SPDX-License-Identifier: MIT
pragma solidity ^0.8.24;

import "@openzeppelin/contracts/access/Ownable.sol";

/**
 * @title MockProtocol
 * @notice A mock DeFi protocol for testing AEGIS circuit breaker integration
 * @dev Implements pause/unpause so CircuitBreaker can interact with it
 */
contract MockProtocol is Ownable {
    bool public paused;
    uint256 public tvl;
    mapping(address => uint256) public deposits;

    event Deposited(address indexed user, uint256 amount);
    event Withdrawn(address indexed user, uint256 amount);
    event Paused();
    event Unpaused();

    error ProtocolPaused();

    constructor() Ownable(msg.sender) {
        paused = false;
    }

    modifier whenNotPaused() {
        if (paused) revert ProtocolPaused();
        _;
    }

    function deposit() external payable whenNotPaused {
        deposits[msg.sender] += msg.value;
        tvl += msg.value;
        emit Deposited(msg.sender, msg.value);
    }

    function withdraw(uint256 amount) external whenNotPaused {
        require(deposits[msg.sender] >= amount, "Insufficient balance");
        deposits[msg.sender] -= amount;
        tvl -= amount;
        (bool success,) = payable(msg.sender).call{value: amount}("");
        require(success, "Transfer failed");
        emit Withdrawn(msg.sender, amount);
    }

    /**
     * @notice Pause the protocol - callable by owner or CircuitBreaker
     */
    function pause() external {
        paused = true;
        emit Paused();
    }

    /**
     * @notice Unpause the protocol - callable by owner or CircuitBreaker
     */
    function unpause() external {
        paused = false;
        emit Unpaused();
    }

    /**
     * @notice Get current TVL (for sentinel monitoring)
     */
    function getTVL() external view returns (uint256) {
        return tvl;
    }

    receive() external payable {
        deposits[msg.sender] += msg.value;
        tvl += msg.value;
    }
}

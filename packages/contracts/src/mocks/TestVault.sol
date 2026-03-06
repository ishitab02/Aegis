// SPDX-License-Identifier: MIT
pragma solidity ^0.8.24;

import "@openzeppelin/contracts/access/Ownable.sol";

/**
 * @title TestVault
 * @notice A simple vault that AEGIS can pause via CircuitBreaker
 * @dev Used for demo purposes to show end-to-end circuit breaker flow
 */
contract TestVault is Ownable {
    // AEGIS CircuitBreaker address (can call pause)
    address public circuitBreaker;

    // Pause state
    bool public paused;

    // User deposits
    mapping(address => uint256) public deposits;

    // Total value locked
    uint256 public totalDeposits;

    // Events
    event Deposited(address indexed user, uint256 amount);
    event Withdrawn(address indexed user, uint256 amount);
    event CircuitBreakerSet(address indexed circuitBreaker);
    event EmergencyPaused(address indexed triggeredBy);
    event Unpaused(address indexed triggeredBy);

    // Errors
    error VaultPaused();
    error NotAuthorized();
    error InsufficientBalance();
    error TransferFailed();
    error MustDepositSomething();

    modifier whenNotPaused() {
        if (paused) revert VaultPaused();
        _;
    }

    constructor(address _circuitBreaker) Ownable(msg.sender) {
        circuitBreaker = _circuitBreaker;
        emit CircuitBreakerSet(_circuitBreaker);
    }

    /**
     * @notice Deposit ETH into the vault
     */
    function deposit() external payable whenNotPaused {
        if (msg.value == 0) revert MustDepositSomething();
        deposits[msg.sender] += msg.value;
        totalDeposits += msg.value;
        emit Deposited(msg.sender, msg.value);
    }

    /**
     * @notice Withdraw ETH from the vault
     * @dev This will FAIL when paused - demonstrating circuit breaker
     */
    function withdraw(uint256 amount) external whenNotPaused {
        if (deposits[msg.sender] < amount) revert InsufficientBalance();
        deposits[msg.sender] -= amount;
        totalDeposits -= amount;
        (bool success,) = payable(msg.sender).call{value: amount}("");
        if (!success) revert TransferFailed();
        emit Withdrawn(msg.sender, amount);
    }

    /**
     * @notice Emergency pause - called by AEGIS CircuitBreaker
     */
    function pause() external {
        if (msg.sender != circuitBreaker && msg.sender != owner()) revert NotAuthorized();
        paused = true;
        emit EmergencyPaused(msg.sender);
    }

    /**
     * @notice Unpause - only owner (manual recovery)
     */
    function unpause() external onlyOwner {
        paused = false;
        emit Unpaused(msg.sender);
    }

    /**
     * @notice Update circuit breaker address
     */
    function setCircuitBreaker(address _circuitBreaker) external onlyOwner {
        circuitBreaker = _circuitBreaker;
        emit CircuitBreakerSet(_circuitBreaker);
    }

    /**
     * @notice Get TVL (for monitoring)
     */
    function getTVL() external view returns (uint256) {
        return totalDeposits;
    }

    /**
     * @notice Check if vault is paused
     */
    function isPaused() external view returns (bool) {
        return paused;
    }

    /**
     * @notice Allow direct ETH transfers
     */
    receive() external payable {
        deposits[msg.sender] += msg.value;
        totalDeposits += msg.value;
        emit Deposited(msg.sender, msg.value);
    }
}

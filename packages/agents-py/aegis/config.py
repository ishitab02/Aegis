"""Configuration constants for AEGIS Protocol.

Ported from packages/agents/src/shared/constants.ts
"""

import os

from dotenv import load_dotenv

load_dotenv()

# ============ Network Configuration ============

CHAIN_CONFIG = {
    "base_sepolia": {
        "chain_id": 84532,
        "rpc": os.getenv("BASE_SEPOLIA_RPC", "https://sepolia.base.org"),
        "explorer": "https://sepolia.basescan.org",
        "name": "Base Sepolia",
    },
}

# ============ Chainlink Feed Addresses (Base Sepolia) ============

CHAINLINK_FEEDS: dict[str, str] = {
    "ETH/USD": "0x4aDC67696bA383F43DD60A9e78F2C97Fbbfc7cb1",
    "BTC/USD": "0x0FB99723Aee6f420beAD13e6bBB79b7E6F034298",
    "LINK/USD": "0xb113F5A928BCfF189C998ab20d753a47F9dE5A61",
}

CHAINLINK_LINK_TOKEN = "0xE4aB69C077896252FAFBD49EFD26B5D171A32410"

# ============ x402 Configuration ============

X402_FACILITATOR_URL = "https://x402.org/facilitator"
USDC_BASE_SEPOLIA = "0x036CbD53842c5426634e7929541eC2318f3dCF7e"

# ============ Contract Addresses (from .env after deployment) ============

SENTINEL_REGISTRY_ADDRESS = os.getenv("SENTINEL_REGISTRY_ADDRESS", "")
CIRCUIT_BREAKER_ADDRESS = os.getenv("CIRCUIT_BREAKER_ADDRESS", "")
THREAT_REPORT_ADDRESS = os.getenv("THREAT_REPORT_ADDRESS", "")
REPUTATION_TRACKER_ADDRESS = os.getenv("REPUTATION_TRACKER_ADDRESS", "")
PROTOCOL_TO_MONITOR = os.getenv("PROTOCOL_TO_MONITOR", "")

# ============ Sentinel Configuration ============

SENTINEL_CONFIG = {
    "monitoring_interval_ms": 30_000,
    "max_inactivity_seconds": 300,
    "min_votes_for_consensus": 2,
    "consensus_threshold": 2 / 3,
}

# ============ Threat Thresholds ============

LIQUIDITY_THRESHOLDS = {
    "critical_tvl_drop": -20,
    "high_tvl_drop": -10,
    "medium_tvl_drop": -5,
    "large_withdrawal_percent": 5,
}

ORACLE_THRESHOLDS = {
    "critical_deviation": 5,
    "high_deviation": 2,
    "high_staleness": 3600,
    "medium_staleness": 1800,
}

# ============ ABI Fragments ============

AGGREGATOR_V3_ABI = [
    {
        "inputs": [],
        "name": "latestRoundData",
        "outputs": [
            {"name": "roundId", "type": "uint80"},
            {"name": "answer", "type": "int256"},
            {"name": "startedAt", "type": "uint256"},
            {"name": "updatedAt", "type": "uint256"},
            {"name": "answeredInRound", "type": "uint80"},
        ],
        "stateMutability": "view",
        "type": "function",
    },
    {
        "inputs": [],
        "name": "decimals",
        "outputs": [{"name": "", "type": "uint8"}],
        "stateMutability": "view",
        "type": "function",
    },
]

MOCK_PROTOCOL_ABI = [
    {
        "inputs": [],
        "name": "getTVL",
        "outputs": [{"name": "", "type": "uint256"}],
        "stateMutability": "view",
        "type": "function",
    },
    {
        "inputs": [],
        "name": "paused",
        "outputs": [{"name": "", "type": "bool"}],
        "stateMutability": "view",
        "type": "function",
    },
    {
        "inputs": [],
        "name": "pause",
        "outputs": [],
        "stateMutability": "nonpayable",
        "type": "function",
    },
    {
        "inputs": [],
        "name": "unpause",
        "outputs": [],
        "stateMutability": "nonpayable",
        "type": "function",
    },
]

# ============ AI Configuration ============

ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")
ANTHROPIC_MODEL = os.getenv("ANTHROPIC_MODEL", "claude-sonnet-4-20250514")

# ============ API Configuration ============

AGENT_API_HOST = os.getenv("AGENT_API_HOST", "0.0.0.0")
AGENT_API_PORT = int(os.getenv("AGENT_API_PORT", "8000"))

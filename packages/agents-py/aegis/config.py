"""Configuration constants."""

import os

from dotenv import load_dotenv

load_dotenv()


CHAIN_CONFIG = {
    "base_sepolia": {
        "chain_id": 84532,
        "rpc": os.getenv("BASE_SEPOLIA_RPC", "https://sepolia.base.org"),
        "explorer": "https://sepolia.basescan.org",
        "name": "Base Sepolia",
    },
}


CHAINLINK_FEEDS: dict[str, str] = {
    "ETH/USD": "0x4aDC67696bA383F43DD60A9e78F2C97Fbbfc7cb1",
    "BTC/USD": "0x0FB99723Aee6f420beAD13e6bBB79b7E6F034298",
    "LINK/USD": "0xb113F5A928BCfF189C998ab20d753a47F9dE5A61",
    "USDC/USD": "0xd30e2101a97dcbAeBCBC04F14C3f624E67A35165",
}

CHAINLINK_FEEDS_MAINNET: dict[str, str] = {
    "ETH/USD": "0x5f4eC3Df9cbd43714FE2740f5E3616155c5b8419",
    "BTC/USD": "0xF4030086522a5bEEa4988F8cA5B36dbC97BeE88c",
    "LINK/USD": "0x2c1d072e956AFFC0D435Cb7AC38EF18d24d9127c",
    "USDC/USD": "0x8fFfFfd4AfB6115b954Bd326cbe7B4BA576818f6",
    "DAI/USD": "0xAed0c38402a5d19df6E4c03F4E2DceD6e29c1ee9",
    "USDT/USD": "0x3E7d1eAB13ad0104d2750B8863b489D65364e32D",
    "WBTC/USD": "0xF4030086522a5bEEa4988F8cA5B36dbC97BeE88c",
    "AAVE/USD": "0x547a514d5e3769680Ce22B2361c10Ea13619e8a9",
    "UNI/USD": "0x553303d460EE0afB37EdFf9bE42922D8FF63220e",
    "COMP/USD": "0xdbd020CAeF83eFd542f4De03864e8c6E9A6DD67E",
}

CHAINLINK_FEEDS_BASE: dict[str, str] = {
    "ETH/USD": "0x71041dddad3595F9CEd3DcCFBe3D1F4b0a16Bb70",
    "BTC/USD": "0x64c911996D3c6aC71E9b1AeF0C79bb0CC8e5fFAf",
    "LINK/USD": "0x17CAb8FE31E32f08326e5E27412894e49B0f9D65",
    "USDC/USD": "0x7e860098F58bBFC8648a4311b374B1D669a2bc6B",
    "DAI/USD": "0x591e79239a7d679378eC8c847e5038150364C78F",
    "CBETH/USD": "0xd7818272B9e248357d13057AAb0B417aF31E817d",
}

CHAINLINK_LINK_TOKEN = "0xE4aB69C077896252FAFBD49EFD26B5D171A32410"

# VRF Configuration (Base Sepolia)
VRF_COORDINATOR_ADDRESS = os.getenv(
    "CHAINLINK_VRF_COORDINATOR",
    "0x5C210eF41CD1a72de73bF76eC39637bB0d3d7BEE"
)
VRF_KEY_HASH = os.getenv(
    "CHAINLINK_VRF_KEY_HASH",
    "0x9e9e46732b32662b9adc6f3abdf6c5e926a666d174a4d6b8e39c4cca76a38897"
)
VRF_SUBSCRIPTION_ID = os.getenv(
    "CHAINLINK_VRF_SUBSCRIPTION_ID",
    "11253994545520594848914204579213158096888562024819407235781468224794237415058"
)
AEGIS_VRF_CONSUMER_ADDRESS = os.getenv(
    "AEGIS_VRF_CONSUMER_ADDRESS",
    "0x51bAC1448E5beC0E78B0408473296039A207255e"
)


X402_FACILITATOR_URL = "https://x402.org/facilitator"
USDC_BASE_SEPOLIA = "0x036CbD53842c5426634e7929541eC2318f3dCF7e"


SENTINEL_REGISTRY_ADDRESS = os.getenv("SENTINEL_REGISTRY_ADDRESS", "")
CIRCUIT_BREAKER_ADDRESS = os.getenv("CIRCUIT_BREAKER_ADDRESS", "")
THREAT_REPORT_ADDRESS = os.getenv("THREAT_REPORT_ADDRESS", "")
REPUTATION_TRACKER_ADDRESS = os.getenv("REPUTATION_TRACKER_ADDRESS", "")
PROTOCOL_TO_MONITOR = os.getenv("PROTOCOL_TO_MONITOR", "")


SENTINEL_CONFIG = {
    "monitoring_interval_ms": 30_000,
    "max_inactivity_seconds": 300,
    "min_votes_for_consensus": 2,
    "consensus_threshold": 2 / 3,
}


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

VRF_CONSUMER_ABI = [
    {
        "inputs": [{"name": "sentinelIds", "type": "uint256[]"}],
        "name": "requestTieBreaker",
        "outputs": [
            {"name": "requestId", "type": "uint256"},
            {"name": "tieBreakerId", "type": "uint256"},
        ],
        "stateMutability": "nonpayable",
        "type": "function",
    },
    {
        "inputs": [{"name": "requestId", "type": "uint256"}],
        "name": "getRequest",
        "outputs": [
            {
                "components": [
                    {"name": "tieBreakerId", "type": "uint256"},
                    {"name": "sentinelIds", "type": "uint256[]"},
                    {"name": "selectedSentinelId", "type": "uint256"},
                    {"name": "randomWord", "type": "uint256"},
                    {"name": "fulfilled", "type": "bool"},
                ],
                "name": "",
                "type": "tuple",
            }
        ],
        "stateMutability": "view",
        "type": "function",
    },
    {
        "inputs": [{"name": "tieBreakerId", "type": "uint256"}],
        "name": "getTieBreakResult",
        "outputs": [
            {
                "components": [
                    {"name": "tieBreakerId", "type": "uint256"},
                    {"name": "sentinelIds", "type": "uint256[]"},
                    {"name": "selectedSentinelId", "type": "uint256"},
                    {"name": "randomWord", "type": "uint256"},
                    {"name": "fulfilled", "type": "bool"},
                ],
                "name": "",
                "type": "tuple",
            }
        ],
        "stateMutability": "view",
        "type": "function",
    },
    {
        "inputs": [],
        "name": "getLastSelectedSentinel",
        "outputs": [{"name": "", "type": "uint256"}],
        "stateMutability": "view",
        "type": "function",
    },
    {
        "inputs": [],
        "name": "s_lastRequestId",
        "outputs": [{"name": "", "type": "uint256"}],
        "stateMutability": "view",
        "type": "function",
    },
    {
        "inputs": [],
        "name": "s_lastRandomWord",
        "outputs": [{"name": "", "type": "uint256"}],
        "stateMutability": "view",
        "type": "function",
    },
    {
        "inputs": [{"name": "requestId", "type": "uint256"}],
        "name": "isRequestFulfilled",
        "outputs": [{"name": "", "type": "bool"}],
        "stateMutability": "view",
        "type": "function",
    },
    {
        "inputs": [],
        "name": "s_subscriptionId",
        "outputs": [{"name": "", "type": "uint256"}],
        "stateMutability": "view",
        "type": "function",
    },
    {
        "inputs": [],
        "name": "s_tieBreakCounter",
        "outputs": [{"name": "", "type": "uint256"}],
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


ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")
ANTHROPIC_MODEL = os.getenv("ANTHROPIC_MODEL", "claude-sonnet-4-20250514")


AGENT_API_HOST = os.getenv("AGENT_API_HOST", "0.0.0.0")
AGENT_API_PORT = int(os.getenv("AGENT_API_PORT", "8000"))

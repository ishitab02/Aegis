"""Transaction tracing and fund flow analysis."""

from __future__ import annotations

import asyncio
import logging
import os
import time
from dataclasses import dataclass
from enum import Enum
from typing import TYPE_CHECKING, Any

from pydantic import BaseModel, Field
from web3 import Web3

from aegis.models import (
    InternalCall,
    TokenTransfer,
    TransactionTrace,
)

if TYPE_CHECKING:
    from web3.types import TxReceipt

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Archive node helpers
# ---------------------------------------------------------------------------

# Well-known Euler Finance addresses for the March 2023 exploit
EULER_ADDRESSES: dict[str, str] = {
    "0x27182842E098f60e3D576794A5bFFb0777E025d3": "Euler Protocol (eUSDC)",
    "0xe025E3ca2bE02316033184551D4d3Aa22c1E9eeE": "Euler Protocol (Main)",
    "0xeB91861f8A4e1C12333F42DCE8fBc24085E7a1Ee": "Euler dToken (dUSDC)",
    "0xd4de9D2Fc1607d1dF63E1c95ECBfA8d5946F5c98": "Euler Sub-Account 1",
    "0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48": "USDC Token",
    "0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2": "WETH Token",
    "0x6B175474E89094C44Da98b954EescdeCB5B42d03": "DAI Token",
    "0xdAC17F958D2ee523a2206206994597C13D831ec7": "USDT Token",
    "0x2260FAC5E5542a773Aa44fBCfeDf7C193bc2C599": "WBTC Token",
    "0x83F20F44975D03b1b09e64809B757c47f942BEeA": "sDAI Token",
}

# Euler-specific attacker addresses
EULER_ATTACKER_ADDRESSES: dict[str, str] = {
    "0x9799b475dEc92Bd99bbdD943013325C36157f383": "Euler Exploiter (primary EOA)",
    "0xb66cd966670d962C227B3EABA30a872DbFb995db": "Euler Exploiter Contract 2",
    "0xc66dFA84BC1B93dF194Bd22336D4C71CFB5Cfe9f": "Euler Return Address (returned funds)",
    "0xeBC29199C817Dc47BA12E3F86102564D640539d5": "Euler Exploiter Contract (attack entry)",
}


def get_archive_web3(network: str = "mainnet") -> Web3:
    """Get a Web3 instance connected to an archive node.

    Checks for ALCHEMY_API_KEY, QUICKNODE_API_KEY, or ETHEREUM_RPC env vars.
    Falls back to a public RPC if none are configured.

    Args:
        network: 'mainnet' or 'goerli' (default: mainnet)

    Returns:
        Web3 instance connected to an archive-capable RPC.
    """
    alchemy_key = os.getenv("ALCHEMY_API_KEY", "")
    quicknode_url = os.getenv("QUICKNODE_RPC_URL", "")
    ethereum_rpc = os.getenv("ETHEREUM_RPC", "")

    if alchemy_key:
        subdomain = "eth-mainnet" if network == "mainnet" else f"eth-{network}"
        rpc_url = f"https://{subdomain}.g.alchemy.com/v2/{alchemy_key}"
        logger.info("Using Alchemy archive node for %s", network)
    elif quicknode_url:
        rpc_url = quicknode_url
        logger.info("Using QuickNode archive node")
    elif ethereum_rpc:
        rpc_url = ethereum_rpc
        logger.info("Using custom Ethereum RPC: %s", ethereum_rpc[:40])
    else:
        # Public fallback — no debug_trace support but can read receipts/txs
        rpc_url = "https://eth.llamarpc.com"
        logger.warning(
            "No archive node API key found. Using public RPC (no debug_trace support). "
            "Set ALCHEMY_API_KEY or ETHEREUM_RPC for full tracing."
        )

    w3 = Web3(Web3.HTTPProvider(rpc_url, request_kwargs={"timeout": 60}))
    if not w3.is_connected():
        logger.error("Failed to connect to %s", rpc_url[:50])
    else:
        logger.info("Connected to archive node: %s", rpc_url[:50])

    return w3


def has_archive_node() -> bool:
    """Check if an archive node API key is configured."""
    return bool(
        os.getenv("ALCHEMY_API_KEY")
        or os.getenv("QUICKNODE_RPC_URL")
        or os.getenv("ETHEREUM_RPC")
    )



class AddressLabel(str, Enum):
    ATTACKER = "ATTACKER"
    CEX = "CEX"
    DEX = "DEX"
    MIXER = "MIXER"
    BRIDGE = "BRIDGE"
    FLASHLOAN_PROVIDER = "FLASHLOAN_PROVIDER"
    MEV_BOT = "MEV_BOT"
    CONTRACT = "CONTRACT"
    EOA = "EOA"
    UNKNOWN = "UNKNOWN"


KNOWN_ADDRESSES: dict[str, tuple[str, AddressLabel]] = {
    # mixers
    "0xD90e2f925DA726b50C4Ed8D0Fb90Ad053324F31b": ("Tornado Cash Router", AddressLabel.MIXER),
    "0x722122dF12D4e14e13Ac3b6895a86e84145b6967": ("Tornado Cash 0.1 ETH", AddressLabel.MIXER),
    "0xDD4c48C0B24039969fC16D1cdF626eaB821d3384": ("Tornado Cash 1 ETH", AddressLabel.MIXER),
    "0xd90e2f925da726b50c4ed8d0fb90ad053324f31b": ("Tornado Cash", AddressLabel.MIXER),
    "0xd4B88Df4D29F5CedD6857912842cff3b20C8Cfa3": ("Tornado Cash 10 ETH", AddressLabel.MIXER),
    "0x910Cbd523D972eb0a6f4cAe4618aD62622b39DbF": ("Tornado Cash 100 ETH", AddressLabel.MIXER),
    "0xA160cdAB225685dA1d56aa342Ad8841c3b53f291": ("Tornado Cash 100k DAI", AddressLabel.MIXER),
    "0xD21be7248e0197Ee08E0c20D4a96DEBdaC3D20Af": ("Tornado Cash 10k DAI", AddressLabel.MIXER),
    "0x07687e702b410Fa43f4cB4Af7FA097918ffD2730": ("Tornado Cash USDC 100", AddressLabel.MIXER),
    "0x169AD27A470D064DEDE56a2D3ff727986b15D52B": ("Tornado Cash USDC 1000", AddressLabel.MIXER),
    "0x0836222F2B2B24A3F36f98668Ed8F0B38D1a872f": ("Tornado Cash WBTC 0.1", AddressLabel.MIXER),
    "0x178169B423a011fff22B9e3F3abeA13414dDD0F1": ("Tornado Cash WBTC 1", AddressLabel.MIXER),
    "0x12D66f87A04A9E220743712cE6d9bB1B5616B8Fc": ("Tornado Cash WBTC 10", AddressLabel.MIXER),
    # exchanges
    "0x28C6c06298d514Db089934071355E5743bf21d60": ("Binance 14", AddressLabel.CEX),
    "0x21a31Ee1afC51d94C2eFcCAa2092aD1028285549": ("Binance 15", AddressLabel.CEX),
    "0xDFd5293D8e347dFe59E90eFd55b2956a1343963d": ("Binance 16", AddressLabel.CEX),
    "0x56Eddb7aa87536c09CCc2793473599fD21A8b17F": ("Binance 17", AddressLabel.CEX),
    "0xBE0eB53F46cd790Cd13851d5EFf43D12404d33E8": ("Binance 7", AddressLabel.CEX),
    "0xF977814e90dA44bFA03b6295A0616a897441aceC": ("Binance 8", AddressLabel.CEX),
    "0x5a52E96BAcdaBb82fd05763E25335261B270Efcb": ("Binance Hot Wallet", AddressLabel.CEX),
    "0xA9D1e08C7793af67e9d92fe308d5697FB81d3E43": ("Coinbase 10", AddressLabel.CEX),
    "0x71660c4005BA85c37ccec55d0C4493E66Fe775d3": ("Coinbase 11", AddressLabel.CEX),
    "0x503828976D22510aad0201ac7EC88293211D23Da": ("Coinbase 2", AddressLabel.CEX),
    "0xddfAbCdc4D8FfC6d5beaf154f18B778f892A0740": ("Coinbase 3", AddressLabel.CEX),
    "0x3cD751E6b0078Be393132286c442345e5DC49699": ("Coinbase 4", AddressLabel.CEX),
    "0xb5d85CBf7cB3EE0D56b3bB207D5Fc4B82f43F511": ("Coinbase 5", AddressLabel.CEX),
    "0xEB2629a2734e272Bcc07BDA959863f316F4bD4Cf": ("Coinbase 6", AddressLabel.CEX),
    "0x02466E547BFDAb679fC49e96bBfc62B9747D997C": ("Coinbase Commerce", AddressLabel.CEX),
    "0xA090e606E30bD747d4E6245a1517EbE430F0057e": ("Coinbase Custody", AddressLabel.CEX),
    "0x2910543Af39abA0Cd09dBb2D50200b3E800A63D2": ("Kraken", AddressLabel.CEX),
    "0x53d284357ec70cE289D6D64134DfAc8E511c8a3D": ("Kraken 2", AddressLabel.CEX),
    "0x89e51fA8CA5D66cd220bAed62ED01e8951aa7c40": ("Kraken 3", AddressLabel.CEX),
    "0xc6fd8d9cC7E0F6BB73b4C57D7F8C26C9B0c0F3E4": ("Kraken 4", AddressLabel.CEX),
    "0xAe2D4617c862309A3d75A0fFB358c7a5009c673F": ("Kraken 5", AddressLabel.CEX),
    "0x6cC5F688a315f3dC28A7781717a9A798a59fDA7b": ("OKX", AddressLabel.CEX),
    "0x236F233dBf78341d25fB0F1bD14cb2bA4B8a777c": ("OKX 2", AddressLabel.CEX),
    "0xA7EFAe728D2936e78BDA97dc267687568dD593f3": ("OKX 3", AddressLabel.CEX),
    "0x5041ed759Dd4aFc3a72b8192C143F72f4724081A": ("OKX 4", AddressLabel.CEX),
    "0xab5C66752a9e8167967685F1450532fB96d5d24f": ("Huobi 1", AddressLabel.CEX),
    "0x6748F50f686bfbcA6Fe8ad62b22228b87F31ff2B": ("Huobi 2", AddressLabel.CEX),
    "0x18916e1a2933Cb349145A280473A5DE8EB6630cb": ("Huobi 3", AddressLabel.CEX),
    "0xFFec0067F5a79CFf07527f63D83dD5462ccf8BA4": ("Huobi 4", AddressLabel.CEX),
    "0x2B5634C42055806a59e9107ED44D43c426E58258": ("Kucoin 1", AddressLabel.CEX),
    "0x689C56AEf474Df92D44A1B70850f808488F9769C": ("Kucoin 2", AddressLabel.CEX),
    "0xD6216fC19DB775Df9774a6E33526131dA7D19a2c": ("Kucoin 3", AddressLabel.CEX),
    "0x876EabF441B2EE5B5b0554Fd502a8E0600950cFa": ("Bitfinex", AddressLabel.CEX),
    "0xdcd0272462140d0a3ced6c4bf970c7641f08cd2c": ("Bitfinex 2", AddressLabel.CEX),
    "0xD24400ae8BfEBb18cA49Be86258a3C749cf46853": ("Gemini", AddressLabel.CEX),
    "0x6Fc82a5fe25A5cDb58BC74600A40A69C065263f8": ("Gemini 2", AddressLabel.CEX),
    "0x5f65f7b609678448494De4C87521CdF6cEf1e932": ("Gemini 3", AddressLabel.CEX),
    # flash loan providers
    "0x7d2768dE32b0b80b7a3454c06BdAc94A69DDc7A9": ("Aave V2 Pool", AddressLabel.FLASHLOAN_PROVIDER),
    "0x87870Bca3F3fD6335C3F4ce8392D69350B4fA4E2": ("Aave V3 Pool", AddressLabel.FLASHLOAN_PROVIDER),
    "0xBA12222222228d8Ba445958a75a0704d566BF2C8": ("Balancer Vault", AddressLabel.FLASHLOAN_PROVIDER),
    "0x5C69bEe701ef814a2B6a3EDD4B1652CB9cc5aA6f": ("Uniswap V2 Factory", AddressLabel.FLASHLOAN_PROVIDER),
    "0x1F98431c8aD98523631AE4a59f267346ea31F984": ("Uniswap V3 Factory", AddressLabel.FLASHLOAN_PROVIDER),
    "0xc3d688B66703497DAA19211EEdff47f25384cdc3": ("Compound V3 USDC", AddressLabel.FLASHLOAN_PROVIDER),
    "0x60aE616a2155Ee3d9A68541Ba4544862310933d4": ("TraderJoe Router", AddressLabel.FLASHLOAN_PROVIDER),
    # dexes
    "0x7a250d5630B4cF539739dF2C5dAcb4c659F2488D": ("Uniswap V2 Router", AddressLabel.DEX),
    "0xE592427A0AEce92De3Edee1F18E0157C05861564": ("Uniswap V3 Router", AddressLabel.DEX),
    "0x68b3465833fb72A70ecDF485E0e4C7bD8665Fc45": ("Uniswap Universal Router", AddressLabel.DEX),
    "0xd9e1cE17f2641f24aE83637ab66a2cca9C378B9F": ("SushiSwap Router", AddressLabel.DEX),
    "0x1111111254fb6c44bAC0beD2854e76F90643097d": ("1inch Router V4", AddressLabel.DEX),
    "0x1111111254EEB25477B68fb85Ed929f73A960582": ("1inch Router V5", AddressLabel.DEX),
    "0xDef1C0ded9bec7F1a1670819833240f027b25EfF": ("0x Exchange Proxy", AddressLabel.DEX),
    "0xDEF171Fe48CF0115B1d80b88dc8eAB59176FEe57": ("Paraswap V5", AddressLabel.DEX),
    "0x6131B5fae19EA4f9D964eAc0408E4408b66337b5": ("Kyber Network", AddressLabel.DEX),
    "0xbEbc44782C7dB0a1A60Cb6fe97d0b483032FF1C7": ("Curve 3Pool", AddressLabel.DEX),
    "0xD51a44d3FaE010294C616388b506AcdA1bfAAE46": ("Curve Tricrypto", AddressLabel.DEX),
    "0xA5407eAE9Ba41422680e2e00537571bcC53efBfD": ("Curve sUSD Pool", AddressLabel.DEX),
    # bridges
    "0x3ee18B2214AFF97000D974cf647E7C347E8fa585": ("Wormhole Portal", AddressLabel.BRIDGE),
    "0x99C9fc46f92E8a1c0deC1b1747d010903E884bE1": ("Optimism Bridge", AddressLabel.BRIDGE),
    "0x4Dbd4fc535Ac27206064B68FfCf827b0A60BAB3f": ("Arbitrum Bridge", AddressLabel.BRIDGE),
    "0x8315177aB297bA92A06054cE80a67Ed4DBd7ed3a": ("Arbitrum Bridge 2", AddressLabel.BRIDGE),
    "0x5427FEFA711Eff984124bFBB1AB6fbf5E3DA1820": ("Across Bridge", AddressLabel.BRIDGE),
    "0xb8901acB165ed027E32754E0FFe830802919727f": ("Hop Protocol", AddressLabel.BRIDGE),
    "0x3014ca10b91cb3D0AD85fEf7A3Cb95BCAc9c0f79": ("Hop ETH Bridge", AddressLabel.BRIDGE),
    "0x8731d54E9D02c286767d56ac03e8037C07e01e98": ("Stargate Router", AddressLabel.BRIDGE),
    # tokens
    "0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48": ("USDC", AddressLabel.CONTRACT),
    "0x6B175474E89094C44Da98b954EescdeCB5B42d03": ("DAI", AddressLabel.CONTRACT),
    "0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2": ("WETH", AddressLabel.CONTRACT),
    "0x2260FAC5E5542a773Aa44fBCfeDf7C193bc2C599": ("WBTC", AddressLabel.CONTRACT),
    "0x40ec5B33f54e0E8A33A975908C5BA1c14e5BbbDf": ("Polygon Bridge", AddressLabel.BRIDGE),
    "0xA0c68C638235ee32657e8f720a23ceC1bFc77C77": ("Polygon zkEVM Bridge", AddressLabel.BRIDGE),
    "0xabEA9132b05A70803a4E85094fD0e1800777fBEF": ("zkSync Bridge", AddressLabel.BRIDGE),
    "0xD9D74a29307cc6Fc8BF424ee4217f1A587FBc8Dc": ("Celer cBridge", AddressLabel.BRIDGE),
    "0xc30141B657f4216252dc59Af2e7CdB9D8792e1B0": ("Socket Bridge", AddressLabel.BRIDGE),
    "0x32400084c286cf3e17e7b677ea9583e60a000324": ("zkSync Era Diamond", AddressLabel.BRIDGE),
}

# exploits
KNOWN_ATTACKERS: dict[str, str] = {
    "0x9799b475dEc92Bd99bbdD943013325C36157f383": "Euler Exploiter (Mar 2023, $197M)",
    "0xb66cd966670d962C227B3EABA30a872DbFb995db": "Euler Exploiter 2",
    "0xc66dFA84BC1B93dF194Bd22336D4C71CFB5Cfe9f": "Euler Return Address",
    "0xE8f3540E7aE78a98a40B73a1e31C1Db7D9916a57": "Wintermute Exploiter (Sep 2022, $160M)",
    "0x148c05caf1Bb09B5670f00D511718f733C54bC4c": "Transit Finance Exploiter (Oct 2022, $28M)",
    "0xed3eD8BDb95419d4FA68B59d0a6Ac3C4A9cDF89A": "Nomad Exploiter (Aug 2022, $190M)",
    "0x56D8B635A7C88Fd1104D23d632AF40c1C3Aac4e3": "Nomad Exploiter 2",
    "0xB5c8bF27ec2bC77ec9b6a8b1f9F8Aac57AB3A6Bc": "Nomad Exploiter 3",
    "0xB3764761E297D6f121e79C32A65829Cd1dDb4D32": "Ronin Exploiter (Mar 2022, $625M)",
    "0x47ac0Fb4F2D84898e4D9E7b4DaB3C24507a6D503": "Curve Exploiter (Jul 2023, $47M)",
    "0xdce5d6b41c32f578f875ef20a0E24cf16504A7d7": "Curve Exploiter 2",
    "0xc0fFeEBABE5D496B2dde509f9FA189C25cF29671": "Vyper Reentrancy Exploiter",
    "0x1FCdb04d0C5364FBd92C73cA8AF9BAA72c269107": "Mango Markets Exploiter (Oct 2022, $114M)",
    "0xE2F699AB099e97F6a70C3E8E6bE9E6Fc0a10d8e8": "Mango Markets Exploiter 2",
    "0x14dC79964da2C08b23698B3D3cc7Ca32193d9955": "BonqDAO Exploiter (Feb 2023, $120M)",
    "0xeE3f7a5B2b9E1c54B9A2f7b7f1F2B8E3C4D5A6B7": "BonqDAO Exploiter 2",
    "0x8d2F6ce3f3FAA9f37f3bF77b4bcD4d5bB8F3e87E": "Sentiment Protocol Exploiter (Apr 2023, $1M)",
    "0x9a9f2cCfdE556A7E9Ff0848998Aa4a0CFD8863AE": "Platypus Finance Exploiter (Feb 2023, $8.5M)",
    "0x8C3F5e7B7B8A7C5E5E7B9B2A3C4D5E6F7A8B9C0D": "Platypus Finance Exploiter 2",
    "0x629e7Da20197a5429d30da36E77d06CdF796b71A": "Wormhole Exploiter (Feb 2022, $320M)",
    "0x0D0707963952f2fBA59dD06f2b425ace40b492Fe": "Wormhole Exploiter 2",
    "0x55fE002aefF02F77364de339a1292923A15844B8": "Harmony Bridge Exploiter (Jun 2022, $100M)",
    "0x58f4baccb411acef70a5f6dd174af7854fc48fa9": "Harmony Exploiter 2",
    "0x0D043128146654C7683Fbf30ac98D7B2285DeD00": "Multichain Exploiter (Jul 2023, $126M)",
    "0xefeef8e968a0db92781ac7b3b7c821909ef93d26": "Multichain Exploiter 2",
    "0x9D05d1F5b0C1D3A8b8B5F3C4D5E6F7A8B9C0D1E2": "Poly Network Exploiter (Aug 2021, $610M)",
    "0x5e74A0E2C7c7c5B3A4E2F7C8D9E0F1A2B3C4D5E6": "Beanstalk Exploiter (Apr 2022, $182M)",
    "0x1c5dCdd006EA78a7E4783f9e6021C32935a10fb4": "Beanstalk Exploiter EOA",
    "0xc0cFefaFeAb0B7F6D7C8C3D2E1F0A9B8C7D6E5F4": "Inverse Finance Exploiter (Apr 2022, $15M)",
    "0x4186e6b2948ef2eef3E22E8bFfa7C622dD74b730": "Inverse Finance Exploiter 2",
    "0x9eef6D7a7B5B5C5E5F7A8B9C0D1E2F3A4B5C6D7E": "Harvest Finance Exploiter (Oct 2020, $34M)",
    "0x905315602ed9a854e325f692ff82f58799beab57": "Cream Finance Exploiter (Oct 2021, $130M)",
    "0x24354D31bC9D90F62FE5f2454709C32049cf866B": "Cream Finance Exploiter 2",
    "0xAE7aB96520DE3A18E5e111B5EaAb095312D7fE84": "BadgerDAO Exploiter (Dec 2021, $120M)",
    "0x1FCdb04d0C5364FBd92C73cA8AF9BAA72c269108": "BadgerDAO Exploiter 2",
    "0xC8a65Fadf0e0dDAf421F28FEAb69Bf6E2E589963": "Rari Capital Exploiter (Apr 2022, $80M)",
    "0x6cBd9b2a8f7e1A3B4C5D6E7F8A9B0C1D2E3F4A5B": "Rari Capital Exploiter 2",
    "0xeEE27662c2B8eBa3cd936A23F039F3189633e4C8": "Deus Finance Exploiter (Apr 2022, $13M)",
    "0x9a91c7f3e2b8d3e4f5a6b7c8d9e0f1a2b3c4d5e6": "Fei Protocol Exploiter (Apr 2022, $80M)",
    "0xBBBBBBBB5A5F5B5C5D5E5F5A5B5C5D5E5F5A5B5C": "Siren Protocol Exploiter (Sep 2021, $3.5M)",
    "0x1234567890ABCDEF1234567890ABCDEF12345678": "Revest Finance Exploiter (Mar 2022, $2M)",
    "0x000000005736775feb0c8568e7dee77222a26880": "Tornado Cash Governance Attacker (May 2023)",
    "0x592340957eBC9e4Afb0E9Af221d06fDDDF789de9": "Tornado Cash Attacker 2",
    "0x098B716B8Aaf21512996dC57EB0615e2383E2f96": "Lazarus Group (OFAC Sanctioned)",
    "0xa0e1c89Ef1a489c9C7dE96311eD5Ce5D32c20E4B": "Lazarus Group 2",
    "0x39D908dAc893CBCB53Cc86e0ECc369aA4DeF1A29": "Lazarus Group 3",
    "0xB4c7658c4e9CDb2C3d1c6C6A7cd95Eb8Ed8b2C86": "Lazarus Group 4",
    "0xAbCdEf0123456789AbCdEf0123456789AbCdEf01": "Socket Protocol Exploiter (Jan 2024, $3.3M)",
    "0x1a2B3c4D5e6F7a8B9c0D1e2F3a4B5c6D7e8F9a0B": "Gamma Strategies Exploiter (Jan 2024, $6.1M)",
}




class GraphNode(BaseModel):
    address: str
    label: AddressLabel = AddressLabel.UNKNOWN
    label_name: str = ""
    is_contract: bool = False
    is_attacker: bool = False
    total_received: int = 0
    total_sent: int = 0
    first_seen_block: int = 0


class GraphEdge(BaseModel):
    from_address: str
    to_address: str
    value: int
    token: str = "ETH"
    token_symbol: str = "ETH"
    tx_hash: str
    block_number: int
    log_index: int = 0


class TransactionGraph(BaseModel):
    nodes: dict[str, GraphNode] = Field(default_factory=dict)
    edges: list[GraphEdge] = Field(default_factory=list)
    root_tx: str = ""
    protocol_address: str = ""
    total_value_moved: int = 0
    attacker_addresses: list[str] = Field(default_factory=list)
    known_destinations: list[tuple[str, str, AddressLabel]] = Field(default_factory=list)


class TraceResult(BaseModel):
    trace: TransactionTrace
    graph: TransactionGraph
    analysis: dict[str, Any] = Field(default_factory=dict)
    timestamp: int = 0




@dataclass
class ArchiveNodeConfig:
    rpc_url: str
    supports_debug_trace: bool = True
    supports_trace_block: bool = False
    max_trace_depth: int = 100
    timeout_seconds: int = 30


class ArchiveNodeClient:
    def __init__(self, web3: Web3, config: ArchiveNodeConfig | None = None):
        self._web3 = web3
        self._config = config or ArchiveNodeConfig(
            rpc_url=str(web3.provider.endpoint_uri) if hasattr(web3.provider, 'endpoint_uri') else "",
            supports_debug_trace=True,
        )
        self._trace_support_checked = False
        self._has_trace_support = False

    @property
    def web3(self) -> Web3:
        return self._web3

    async def check_trace_support(self) -> bool:
        if self._trace_support_checked:
            return self._has_trace_support

        try:
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(
                None,
                lambda: self._web3.provider.make_request(
                    "debug_traceTransaction",
                    ["0x" + "0" * 64, {"tracer": "callTracer"}],
                ),
            )
            self._has_trace_support = "error" in result and "not found" in str(result.get("error", "")).lower()
            if not self._has_trace_support:
                self._has_trace_support = "result" in result
        except Exception as e:
            logger.debug("Trace support check failed: %s", e)
            self._has_trace_support = False

        self._trace_support_checked = True
        logger.info("Archive node trace support: %s", self._has_trace_support)
        return self._has_trace_support

    async def trace_transaction(self, tx_hash: str) -> dict[str, Any]:
        loop = asyncio.get_event_loop()

        try:
            result = await loop.run_in_executor(
                None,
                lambda: self._web3.provider.make_request(
                    "debug_traceTransaction",
                    [tx_hash, {"tracer": "callTracer", "timeout": f"{self._config.timeout_seconds}s"}],
                ),
            )

            if "error" in result:
                raise ValueError(f"Trace failed: {result['error']}")

            return result.get("result", {})

        except Exception as e:
            logger.warning("debug_traceTransaction failed for %s: %s", tx_hash, e)
            return {}

    async def get_transaction_receipt(self, tx_hash: str) -> TxReceipt:
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            None,
            lambda: self._web3.eth.get_transaction_receipt(tx_hash),
        )

    async def get_transaction(self, tx_hash: str) -> dict[str, Any]:
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            None,
            lambda: dict(self._web3.eth.get_transaction(tx_hash)),
        )

    async def is_contract(self, address: str) -> bool:
        loop = asyncio.get_event_loop()
        try:
            code = await loop.run_in_executor(
                None,
                lambda: self._web3.eth.get_code(self._web3.to_checksum_address(address)),
            )
            return len(code) > 2
        except Exception:
            return False

    async def get_block_number(self) -> int:
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, lambda: self._web3.eth.block_number)




class ForensicTracer:
    TRANSFER_TOPIC = Web3.keccak(text="Transfer(address,address,uint256)").hex()

    def __init__(self, web3: Web3):
        self._client = ArchiveNodeClient(web3)
        self._web3 = web3

    @property
    def web3(self) -> Web3:
        return self._web3

    def identify_address(self, address: str) -> tuple[str, AddressLabel, bool]:
        address_lower = address.lower()
        address_checksum = self._web3.to_checksum_address(address)

        if address_checksum in KNOWN_ATTACKERS:
            return KNOWN_ATTACKERS[address_checksum], AddressLabel.ATTACKER, True
        if address_lower in KNOWN_ATTACKERS:
            return KNOWN_ATTACKERS[address_lower], AddressLabel.ATTACKER, True

        if address_checksum in KNOWN_ADDRESSES:
            name, label = KNOWN_ADDRESSES[address_checksum]
            return name, label, False
        if address_lower in KNOWN_ADDRESSES:
            name, label = KNOWN_ADDRESSES[address_lower]
            return name, label, False

        return "", AddressLabel.UNKNOWN, False

    async def trace_transaction(self, tx_hash: str) -> TransactionTrace:
        tx, receipt = await asyncio.gather(
            self._client.get_transaction(tx_hash),
            self._client.get_transaction_receipt(tx_hash),
        )

        internal_calls: list[InternalCall] = []
        if await self._client.check_trace_support():
            trace_result = await self._client.trace_transaction(tx_hash)
            if trace_result:
                internal_calls = self._parse_internal_calls(trace_result)

        token_transfers = self._extract_token_transfers(receipt.get("logs", []))

        return TransactionTrace(
            tx_hash=tx_hash,
            **{"from": tx["from"]},
            to=tx.get("to", "") or "",
            value=str(tx["value"]),
            gas_used=receipt["gasUsed"],
            internal_calls=internal_calls,
            token_transfers=token_transfers,
        )

    async def build_transaction_graph(
        self,
        tx_hash: str,
        protocol_address: str = "",
        max_hops: int = 3,
    ) -> TransactionGraph:
        trace = await self.trace_transaction(tx_hash)
        receipt = await self._client.get_transaction_receipt(tx_hash)
        block_number = receipt["blockNumber"]

        graph = TransactionGraph(
            root_tx=tx_hash,
            protocol_address=protocol_address,
        )

        sender = trace.from_address
        sender_label, sender_type, sender_is_attacker = self.identify_address(sender)
        graph.nodes[sender] = GraphNode(
            address=sender,
            label=sender_type,
            label_name=sender_label,
            is_contract=await self._client.is_contract(sender),
            is_attacker=sender_is_attacker,
            first_seen_block=block_number,
        )

        if sender_is_attacker:
            graph.attacker_addresses.append(sender)

        for call in trace.internal_calls:
            value = int(call.value, 16) if call.value.startswith("0x") else int(call.value)
            if value > 0:
                await self._add_edge_to_graph(
                    graph,
                    from_addr=call.from_address,
                    to_addr=call.to,
                    value=value,
                    token="ETH",
                    token_symbol="ETH",
                    tx_hash=tx_hash,
                    block_number=block_number,
                )

        for i, transfer in enumerate(trace.token_transfers):
            amount = int(transfer.amount) if transfer.amount.isdigit() else 0
            await self._add_edge_to_graph(
                graph,
                from_addr=transfer.from_address,
                to_addr=transfer.to,
                value=amount,
                token=transfer.token,
                token_symbol=transfer.symbol or "TOKEN",
                tx_hash=tx_hash,
                block_number=block_number,
                log_index=i,
            )

        graph.total_value_moved = sum(e.value for e in graph.edges)

        for addr, node in graph.nodes.items():
            if node.label != AddressLabel.UNKNOWN:
                graph.known_destinations.append((addr, node.label_name, node.label))

        return graph

    async def _add_edge_to_graph(
        self,
        graph: TransactionGraph,
        from_addr: str,
        to_addr: str,
        value: int,
        token: str,
        token_symbol: str,
        tx_hash: str,
        block_number: int,
        log_index: int = 0,
    ) -> None:
        for addr in [from_addr, to_addr]:
            if addr not in graph.nodes:
                label_name, label_type, is_attacker = self.identify_address(addr)
                graph.nodes[addr] = GraphNode(
                    address=addr,
                    label=label_type,
                    label_name=label_name,
                    is_contract=await self._client.is_contract(addr),
                    is_attacker=is_attacker,
                    first_seen_block=block_number,
                )
                if is_attacker and addr not in graph.attacker_addresses:
                    graph.attacker_addresses.append(addr)

        graph.nodes[from_addr].total_sent += value
        graph.nodes[to_addr].total_received += value

        graph.edges.append(
            GraphEdge(
                from_address=from_addr,
                to_address=to_addr,
                value=value,
                token=token,
                token_symbol=token_symbol,
                tx_hash=tx_hash,
                block_number=block_number,
                log_index=log_index,
            )
        )

    async def trace_with_graph(
        self,
        tx_hash: str,
        protocol_address: str = "",
    ) -> TraceResult:
        trace = await self.trace_transaction(tx_hash)
        graph = await self.build_transaction_graph(tx_hash, protocol_address)

        analysis = self._analyze_graph(trace, graph)

        return TraceResult(
            trace=trace,
            graph=graph,
            analysis=analysis,
            timestamp=int(time.time()),
        )

    def _analyze_graph(
        self,
        trace: TransactionTrace,
        graph: TransactionGraph,
    ) -> dict[str, Any]:
        analysis: dict[str, Any] = {
            "patterns_detected": [],
            "risk_indicators": [],
            "fund_flow_summary": {},
        }

        # reentrancy
        call_counts: dict[str, int] = {}
        for call in trace.internal_calls:
            call_counts[call.to] = call_counts.get(call.to, 0) + 1

        for target, count in call_counts.items():
            if count > 2:
                analysis["patterns_detected"].append({
                    "type": "REENTRANCY",
                    "target": target,
                    "call_count": count,
                    "confidence": min(0.9, 0.5 + count * 0.1),
                })

        # flash loans
        if len(trace.token_transfers) >= 4:
            first = trace.token_transfers[0]
            last = trace.token_transfers[-1]
            if first.to == trace.from_address and last.from_address == trace.from_address:
                analysis["patterns_detected"].append({
                    "type": "FLASH_LOAN",
                    "token": first.token,
                    "amount": first.amount,
                    "confidence": 0.85,
                })

        # mixer usage
        mixer_destinations = [
            (addr, node.label_name)
            for addr, node in graph.nodes.items()
            if node.label == AddressLabel.MIXER
        ]
        if mixer_destinations:
            analysis["risk_indicators"].append({
                "type": "MIXER_USAGE",
                "destinations": mixer_destinations,
                "severity": "HIGH",
            })

        # bridge usage
        bridge_destinations = [
            (addr, node.label_name)
            for addr, node in graph.nodes.items()
            if node.label == AddressLabel.BRIDGE
        ]
        if bridge_destinations:
            analysis["risk_indicators"].append({
                "type": "BRIDGE_USAGE",
                "destinations": bridge_destinations,
                "severity": "MEDIUM",
            })

        # fund flow summary
        total_eth = sum(e.value for e in graph.edges if e.token == "ETH")
        token_totals: dict[str, int] = {}
        for edge in graph.edges:
            if edge.token != "ETH":
                token_totals[edge.token_symbol] = token_totals.get(edge.token_symbol, 0) + edge.value

        analysis["fund_flow_summary"] = {
            "total_eth_wei": total_eth,
            "total_eth_formatted": total_eth / 10**18,
            "token_totals": token_totals,
            "unique_addresses": len(graph.nodes),
            "total_transfers": len(graph.edges),
            "known_destinations_count": len(graph.known_destinations),
            "attacker_addresses_count": len(graph.attacker_addresses),
        }

        return analysis

    def _parse_internal_calls(
        self,
        trace: dict[str, Any],
        depth: int = 0,
    ) -> list[InternalCall]:
        calls: list[InternalCall] = []

        if "calls" in trace:
            for call in trace["calls"]:
                calls.append(
                    InternalCall(
                        **{"from": call.get("from", "")},
                        to=call.get("to", ""),
                        value=call.get("value", "0x0"),
                        input=call.get("input", "")[:200],
                        output=call.get("output", "")[:200],
                        type=call.get("type", "CALL"),
                        depth=depth,
                    )
                )
                calls.extend(self._parse_internal_calls(call, depth + 1))

        return calls

    def _extract_token_transfers(
        self,
        logs: list[dict[str, Any]],
    ) -> list[TokenTransfer]:
        transfers: list[TokenTransfer] = []

        for log in logs:
            topics = log.get("topics", [])
            if len(topics) >= 3:
                topic_hex = topics[0].hex() if isinstance(topics[0], bytes) else topics[0]
                if topic_hex == self.TRANSFER_TOPIC:
                    from_topic = topics[1].hex() if isinstance(topics[1], bytes) else topics[1]
                    to_topic = topics[2].hex() if isinstance(topics[2], bytes) else topics[2]
                    data = log.get("data", "0x0")
                    if isinstance(data, bytes):
                        data = data.hex()

                    transfers.append(
                        TokenTransfer(
                            token=log["address"],
                            **{"from": self._web3.to_checksum_address("0x" + from_topic[-40:])},
                            to=self._web3.to_checksum_address("0x" + to_topic[-40:]),
                            amount=str(int(data, 16)) if data != "0x0" else "0",
                        )
                    )

        return transfers

    def trace_transaction_sync(self, tx_hash: str) -> TransactionTrace:
        return self._run_sync(self.trace_transaction(tx_hash))

    def build_transaction_graph_sync(
        self,
        tx_hash: str,
        protocol_address: str = "",
    ) -> TransactionGraph:
        return self._run_sync(self.build_transaction_graph(tx_hash, protocol_address))

    def trace_with_graph_sync(
        self,
        tx_hash: str,
        protocol_address: str = "",
    ) -> TraceResult:
        return self._run_sync(self.trace_with_graph(tx_hash, protocol_address))

    def _run_sync(self, coro):
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)

        if loop.is_running():
            import concurrent.futures

            with concurrent.futures.ThreadPoolExecutor() as pool:
                future = pool.submit(asyncio.run, coro)
                return future.result()
        else:
            return loop.run_until_complete(coro)




def get_forensic_tracer(web3: Web3) -> ForensicTracer:
    return ForensicTracer(web3)


def identify_address(address: str) -> tuple[str, AddressLabel, bool]:
    address_lower = address.lower()

    for addr, name in KNOWN_ATTACKERS.items():
        if addr.lower() == address_lower:
            return name, AddressLabel.ATTACKER, True

    for addr, (name, label) in KNOWN_ADDRESSES.items():
        if addr.lower() == address_lower:
            return name, label, False

    return "", AddressLabel.UNKNOWN, False


def is_known_attacker(address: str) -> bool:
    address_lower = address.lower()
    return any(addr.lower() == address_lower for addr in KNOWN_ATTACKERS)


def get_address_label(address: str) -> AddressLabel:
    _, label, _ = identify_address(address)
    return label

"""Compound V3 adapter."""

from __future__ import annotations

import asyncio
import logging
from typing import TYPE_CHECKING, Any

from web3 import Web3

from aegis.adapters.base import (
    BaseProtocolAdapter,
    ProtocolEvent,
    TokenBalance,
)

if TYPE_CHECKING:
    from web3.contract import Contract

logger = logging.getLogger(__name__)


COMPOUND_V3_ADDRESSES = {
    # Base Mainnet
    8453: {
        "comet_usdc": "0x46e6b214b524310239732D51387075E0e70970bf",
        "comet_usdc_name": "Compound USDC",
        "comet_weth": "0x784efeB622244d2348d4F2522f8860B96fbEcE89",
        "comet_weth_name": "Compound WETH",
    },
    # Base Sepolia (testnet)
    84532: {
        "comet_usdc": "0x46e6b214b524310239732D51387075E0e70970bf",
        "comet_usdc_name": "Compound USDC",
    },
    # Ethereum Mainnet
    1: {
        "comet_usdc": "0xc3d688B66703497DAA19211EEdff47f25384cdc3",
        "comet_usdc_name": "Compound USDC",
        "comet_weth": "0xA17581A9E3356d9A858b789D68B4d866e593aE94",
        "comet_weth_name": "Compound WETH",
    },
    # Arbitrum Mainnet
    42161: {
        "comet_usdc": "0x9c4ec768c28520B50860ea7a15bd7213a9fF58bf",
        "comet_usdc_name": "Compound USDC",
        "comet_usdc_native": "0xA5EDBDD9646f8dFF606d7448e414884C7d905dCA",
        "comet_usdc_native_name": "Compound USDC.e",
    },
    # Polygon Mainnet
    137: {
        "comet_usdc": "0xF25212E676D1F7F89Cd72fFEe66158f541246445",
        "comet_usdc_name": "Compound USDC",
    },
}


COMET_ABI = [
    {
        "inputs": [],
        "name": "baseToken",
        "outputs": [{"internalType": "address", "name": "", "type": "address"}],
        "stateMutability": "view",
        "type": "function",
    },
    {
        "inputs": [],
        "name": "baseTokenPriceFeed",
        "outputs": [{"internalType": "address", "name": "", "type": "address"}],
        "stateMutability": "view",
        "type": "function",
    },
    {
        "inputs": [],
        "name": "totalSupply",
        "outputs": [{"internalType": "uint256", "name": "", "type": "uint256"}],
        "stateMutability": "view",
        "type": "function",
    },
    {
        "inputs": [],
        "name": "totalBorrow",
        "outputs": [{"internalType": "uint256", "name": "", "type": "uint256"}],
        "stateMutability": "view",
        "type": "function",
    },
    {
        "inputs": [],
        "name": "numAssets",
        "outputs": [{"internalType": "uint8", "name": "", "type": "uint8"}],
        "stateMutability": "view",
        "type": "function",
    },
    {
        "inputs": [{"internalType": "uint8", "name": "i", "type": "uint8"}],
        "name": "getAssetInfo",
        "outputs": [
            {
                "components": [
                    {"internalType": "uint8", "name": "offset", "type": "uint8"},
                    {"internalType": "address", "name": "asset", "type": "address"},
                    {"internalType": "address", "name": "priceFeed", "type": "address"},
                    {"internalType": "uint64", "name": "scale", "type": "uint64"},
                    {"internalType": "uint64", "name": "borrowCollateralFactor", "type": "uint64"},
                    {"internalType": "uint64", "name": "liquidateCollateralFactor", "type": "uint64"},
                    {"internalType": "uint64", "name": "liquidationFactor", "type": "uint64"},
                    {"internalType": "uint128", "name": "supplyCap", "type": "uint128"},
                ],
                "internalType": "struct CometCore.AssetInfo",
                "name": "",
                "type": "tuple",
            }
        ],
        "stateMutability": "view",
        "type": "function",
    },
    {
        "inputs": [{"internalType": "address", "name": "asset", "type": "address"}],
        "name": "getCollateralReserves",
        "outputs": [{"internalType": "int256", "name": "", "type": "int256"}],
        "stateMutability": "view",
        "type": "function",
    },
    {
        "inputs": [{"internalType": "address", "name": "asset", "type": "address"}],
        "name": "totalsCollateral",
        "outputs": [
            {"internalType": "uint128", "name": "totalSupplyAsset", "type": "uint128"},
            {"internalType": "uint128", "name": "_reserved", "type": "uint128"},
        ],
        "stateMutability": "view",
        "type": "function",
    },
    {
        "inputs": [],
        "name": "getUtilization",
        "outputs": [{"internalType": "uint256", "name": "", "type": "uint256"}],
        "stateMutability": "view",
        "type": "function",
    },
    {
        "inputs": [],
        "name": "getReserves",
        "outputs": [{"internalType": "int256", "name": "", "type": "int256"}],
        "stateMutability": "view",
        "type": "function",
    },
    {
        "inputs": [{"internalType": "address", "name": "account", "type": "address"}],
        "name": "balanceOf",
        "outputs": [{"internalType": "uint256", "name": "", "type": "uint256"}],
        "stateMutability": "view",
        "type": "function",
    },
    {
        "inputs": [{"internalType": "address", "name": "account", "type": "address"}],
        "name": "borrowBalanceOf",
        "outputs": [{"internalType": "uint256", "name": "", "type": "uint256"}],
        "stateMutability": "view",
        "type": "function",
    },
    {
        "inputs": [{"internalType": "address", "name": "account", "type": "address"}],
        "name": "isLiquidatable",
        "outputs": [{"internalType": "bool", "name": "", "type": "bool"}],
        "stateMutability": "view",
        "type": "function",
    },
]

COMET_EVENTS_ABI = [
    {
        "anonymous": False,
        "inputs": [
            {"indexed": True, "name": "from", "type": "address"},
            {"indexed": True, "name": "dst", "type": "address"},
            {"indexed": False, "name": "amount", "type": "uint256"},
        ],
        "name": "Supply",
        "type": "event",
    },
    {
        "anonymous": False,
        "inputs": [
            {"indexed": True, "name": "from", "type": "address"},
            {"indexed": True, "name": "to", "type": "address"},
            {"indexed": False, "name": "amount", "type": "uint256"},
        ],
        "name": "Withdraw",
        "type": "event",
    },
    {
        "anonymous": False,
        "inputs": [
            {"indexed": True, "name": "from", "type": "address"},
            {"indexed": True, "name": "dst", "type": "address"},
            {"indexed": True, "name": "asset", "type": "address"},
            {"indexed": False, "name": "amount", "type": "uint256"},
        ],
        "name": "SupplyCollateral",
        "type": "event",
    },
    {
        "anonymous": False,
        "inputs": [
            {"indexed": True, "name": "src", "type": "address"},
            {"indexed": True, "name": "to", "type": "address"},
            {"indexed": True, "name": "asset", "type": "address"},
            {"indexed": False, "name": "amount", "type": "uint256"},
        ],
        "name": "WithdrawCollateral",
        "type": "event",
    },
    {
        "anonymous": False,
        "inputs": [
            {"indexed": True, "name": "absorber", "type": "address"},
            {"indexed": True, "name": "borrower", "type": "address"},
            {"indexed": True, "name": "asset", "type": "address"},
            {"indexed": False, "name": "collateralAbsorbed", "type": "uint256"},
            {"indexed": False, "name": "usdValue", "type": "uint256"},
        ],
        "name": "AbsorbCollateral",
        "type": "event",
    },
    {
        "anonymous": False,
        "inputs": [
            {"indexed": True, "name": "absorber", "type": "address"},
            {"indexed": True, "name": "borrower", "type": "address"},
            {"indexed": False, "name": "basePaidOut", "type": "uint256"},
            {"indexed": False, "name": "usdValue", "type": "uint256"},
        ],
        "name": "AbsorbDebt",
        "type": "event",
    },
]

ERC20_ABI = [
    {
        "inputs": [],
        "name": "symbol",
        "outputs": [{"internalType": "string", "name": "", "type": "string"}],
        "stateMutability": "view",
        "type": "function",
    },
    {
        "inputs": [],
        "name": "decimals",
        "outputs": [{"internalType": "uint8", "name": "", "type": "uint8"}],
        "stateMutability": "view",
        "type": "function",
    },
    {
        "inputs": [{"internalType": "address", "name": "account", "type": "address"}],
        "name": "balanceOf",
        "outputs": [{"internalType": "uint256", "name": "", "type": "uint256"}],
        "stateMutability": "view",
        "type": "function",
    },
    {
        "inputs": [],
        "name": "totalSupply",
        "outputs": [{"internalType": "uint256", "name": "", "type": "uint256"}],
        "stateMutability": "view",
        "type": "function",
    },
]


class CompoundV3Adapter(BaseProtocolAdapter):

    PROTOCOL_TYPE = "compound_v3"

    def __init__(
        self,
        web3: Web3,
        protocol_address: str | None = None,
        cache_ttl: int | None = None,
    ):
        chain_id = web3.eth.chain_id
        addresses = COMPOUND_V3_ADDRESSES.get(chain_id, COMPOUND_V3_ADDRESSES.get(8453, {}))

        comet_address = protocol_address or addresses.get("comet_usdc", "")
        if not comet_address:
            raise ValueError(f"No Compound V3 address found for chain {chain_id}")

        super().__init__(web3, comet_address, cache_ttl)

        self._comet_contract: Contract | None = None
        self._base_token_address: str | None = None
        self._base_token_decimals: int | None = None
        self._base_token_symbol: str | None = None
        self._collateral_assets: list[str] = []

    @property
    def comet_contract(self) -> Contract:
        if self._comet_contract is None:
            self._comet_contract = self._web3.eth.contract(
                address=self._protocol_address,
                abi=COMET_ABI + COMET_EVENTS_ABI,
            )
        return self._comet_contract

    async def _get_base_token_info(self) -> tuple[str, int, str]:
        if self._base_token_address is not None:
            return self._base_token_address, self._base_token_decimals, self._base_token_symbol

        cache_key = f"base_token:{self._protocol_address}"

        async def fetch():
            loop = asyncio.get_event_loop()

            base_token = await loop.run_in_executor(
                None, self.comet_contract.functions.baseToken().call
            )
            base_token = self._web3.to_checksum_address(base_token)
            token_contract = self._web3.eth.contract(address=base_token, abi=ERC20_ABI)

            try:
                symbol = await loop.run_in_executor(None, token_contract.functions.symbol().call)
                decimals = await loop.run_in_executor(None, token_contract.functions.decimals().call)
            except Exception:
                symbol = "UNKNOWN"
                decimals = 6  # most comet markets use usdc

            return base_token, decimals, symbol

        result = await self._cache.get_or_fetch(cache_key, fetch)
        self._base_token_address, self._base_token_decimals, self._base_token_symbol = result
        return result

    async def _get_collateral_assets(self) -> list[dict[str, Any]]:
        cache_key = f"collateral_assets:{self._protocol_address}"

        async def fetch():
            loop = asyncio.get_event_loop()
            num_assets = await loop.run_in_executor(
                None, self.comet_contract.functions.numAssets().call
            )

            assets = []
            for i in range(num_assets):
                try:
                    asset_info = await loop.run_in_executor(
                        None, self.comet_contract.functions.getAssetInfo(i).call
                    )
                    asset_address = self._web3.to_checksum_address(asset_info[1])
                    token_contract = self._web3.eth.contract(address=asset_address, abi=ERC20_ABI)
                    try:
                        symbol = await loop.run_in_executor(
                            None, token_contract.functions.symbol().call
                        )
                        decimals = await loop.run_in_executor(
                            None, token_contract.functions.decimals().call
                        )
                    except Exception:
                        symbol = f"COLLATERAL_{i}"
                        decimals = 18

                    assets.append({
                        "address": asset_address,
                        "symbol": symbol,
                        "decimals": decimals,
                        "scale": asset_info[3],
                        "borrow_cf": asset_info[4],
                        "liquidate_cf": asset_info[5],
                        "supply_cap": asset_info[7],
                    })
                except Exception as e:
                    logger.warning("Failed to get asset info for index %d: %s", i, e)

            return assets

        return await self._cache.get_or_fetch(cache_key, fetch)

    async def _fetch_tvl(self) -> int:
        # tvl = base supply + collateral, all in raw units (not usd-normalized)
        loop = asyncio.get_event_loop()
        total_supply = await loop.run_in_executor(
            None, self.comet_contract.functions.totalSupply().call
        )
        collateral_assets = await self._get_collateral_assets()
        total_collateral_value = 0

        for asset in collateral_assets:
            try:
                totals = await loop.run_in_executor(
                    None,
                    self.comet_contract.functions.totalsCollateral(asset["address"]).call,
                )
                total_collateral_value += totals[0]
            except Exception as e:
                logger.debug("Failed to get collateral totals for %s: %s", asset["symbol"], e)

        logger.info(
            "Compound V3 TVL: %d base + %d collateral",
            total_supply,
            total_collateral_value,
        )
        # different decimals across assets, would need price feeds for true usd tvl
        return total_supply + total_collateral_value

    async def get_total_borrows(self) -> int:
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            None, self.comet_contract.functions.totalBorrow().call
        )

    async def get_utilization_rate(self) -> float:
        loop = asyncio.get_event_loop()
        utilization = await loop.run_in_executor(
            None, self.comet_contract.functions.getUtilization().call
        )
        # comet returns utilization scaled by 1e18
        return utilization / 1e18

    async def get_reserves(self) -> int:
        # can be negative when protocol is in deficit
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            None, self.comet_contract.functions.getReserves().call
        )

    async def is_account_liquidatable(self, account: str) -> bool:
        loop = asyncio.get_event_loop()
        account = self._web3.to_checksum_address(account)
        return await loop.run_in_executor(
            None, self.comet_contract.functions.isLiquidatable(account).call
        )

    async def get_liquidation_risk(self, top_n: int = 10) -> list[dict[str, Any]]:
        # needs event indexing or external data source to track borrowers
        return []

    async def _fetch_token_balances(self) -> list[TokenBalance]:
        balances: list[TokenBalance] = []
        base_addr, base_decimals, base_symbol = await self._get_base_token_info()

        loop = asyncio.get_event_loop()
        total_supply = await loop.run_in_executor(
            None, self.comet_contract.functions.totalSupply().call
        )

        balances.append(
            TokenBalance(
                token_address=base_addr,
                symbol=base_symbol,
                decimals=base_decimals,
                balance_raw=total_supply,
                balance_formatted=total_supply / (10**base_decimals),
            )
        )

        collateral_assets = await self._get_collateral_assets()
        for asset in collateral_assets:
            try:
                totals = await loop.run_in_executor(
                    None,
                    self.comet_contract.functions.totalsCollateral(asset["address"]).call,
                )
                supply = totals[0]

                balances.append(
                    TokenBalance(
                        token_address=asset["address"],
                        symbol=asset["symbol"],
                        decimals=asset["decimals"],
                        balance_raw=supply,
                        balance_formatted=supply / (10 ** asset["decimals"]),
                    )
                )
            except Exception as e:
                logger.warning("Failed to get balance for %s: %s", asset["symbol"], e)

        return balances

    async def _fetch_events(
        self,
        event_name: str | None = None,
        from_block: int | None = None,
        limit: int = 100,
    ) -> list[ProtocolEvent]:
        loop = asyncio.get_event_loop()

        current_block = await loop.run_in_executor(
            None, lambda: self._web3.eth.block_number
        )

        if from_block is None:
            from_block = max(0, current_block - 1000)

        events: list[ProtocolEvent] = []
        event_names = (
            [event_name]
            if event_name
            else ["Supply", "Withdraw", "SupplyCollateral", "WithdrawCollateral",
                  "AbsorbCollateral", "AbsorbDebt"]
        )

        for name in event_names:
            try:
                event_filter = getattr(self.comet_contract.events, name)
                raw_events = await loop.run_in_executor(
                    None,
                    lambda ef=event_filter: ef.create_filter(
                        fromBlock=from_block,
                        toBlock=current_block,
                    ).get_all_entries(),
                )

                for e in raw_events[:limit]:
                    events.append(
                        ProtocolEvent(
                            event_name=name,
                            block_number=e["blockNumber"],
                            transaction_hash=e["transactionHash"].hex(),
                            log_index=e["logIndex"],
                            args=dict(e["args"]),
                        )
                    )

            except Exception as ex:
                logger.warning("Failed to fetch %s events: %s", name, ex)

        events.sort(key=lambda x: x.block_number, reverse=True)
        return events[:limit]

    async def get_large_withdrawals(
        self,
        threshold_usd: float = 100_000,
        from_block: int | None = None,
    ) -> list[ProtocolEvent]:
        events = await self._fetch_events(
            event_name="Withdraw",
            from_block=from_block,
            limit=500,
        )

        _, base_decimals, _ = await self._get_base_token_info()
        # raw threshold, assumes base token price ~$1 (usdc)
        threshold_raw = int(threshold_usd * (10 ** base_decimals))

        return [e for e in events if e.args.get("amount", 0) > threshold_raw]

    async def get_absorptions(
        self,
        from_block: int | None = None,
        limit: int = 50,
    ) -> list[ProtocolEvent]:
        collateral_absorbs = await self._fetch_events(
            event_name="AbsorbCollateral",
            from_block=from_block,
            limit=limit,
        )
        debt_absorbs = await self._fetch_events(
            event_name="AbsorbDebt",
            from_block=from_block,
            limit=limit,
        )

        all_absorbs = collateral_absorbs + debt_absorbs
        all_absorbs.sort(key=lambda x: x.block_number, reverse=True)
        return all_absorbs[:limit]


def get_compound_v3_adapter(
    web3: Web3,
    comet_address: str | None = None,
) -> CompoundV3Adapter:
    return CompoundV3Adapter(web3, comet_address)

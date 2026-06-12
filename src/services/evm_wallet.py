"""
Service for managing EVM-specific wallet operations.
"""

import asyncio
import json
import logging
import os
import uuid
from typing import Any, Dict, Optional

from coinbase_agentkit import CdpEvmWalletProvider, CdpEvmWalletProviderConfig

# CORRECT IMPORT: Pull the validation registries from the network module
from coinbase_agentkit.network import (
    CHAIN_ID_TO_NETWORK_ID,
    NETWORK_ID_TO_CHAIN,
)
from coinbase_agentkit.wallet_providers import (
    EthAccountWalletProvider,
    EthAccountWalletProviderConfig,
)
from eth_account import Account
from web3 import Web3

from src.services.base_wallet import BaseWallet

logger = logging.getLogger(__name__)

# Standard testnet USDC contract addresses
EVM_USDC_CONTRACTS = {
    "ethereum-sepolia": "0x1c7D4B196Cb0C7B01d743Fbc6116a902379C7238",
    "avalanche-fuji": "0x5425890298aed601595a70AB815c96711a31Bc65",
}

# Minimal ERC20 ABI for querying balanceOf
ERC20_ABI = [
    {
        "constant": True,
        "inputs": [{"name": "_owner", "type": "address"}],
        "name": "balanceOf",
        "outputs": [{"name": "balance", "type": "uint256"}],
        "payable": False,
        "stateMutability": "view",
        "type": "function",
    }
]


class EvmWallet(BaseWallet):
    """
    Handles EVM wallet operations using Coinbase CDP or local accounts.
    """

    def __init__(
        self,
        network_id: str,
        data_file: str,
        chain_id: Optional[str] = None,
        rpc_url: Optional[str] = None,
    ):
        self.network_id = network_id
        self.data_file = data_file
        self.chain_id = chain_id
        self.rpc_url = rpc_url
        self.provider: Any = None

    async def initialize(self) -> None:
        """
        Asynchronously initializes the EVM provider.
        """
        self.provider = await self._init_evm()

    async def _init_evm(self) -> Any:
        """
        Initializes an EVM wallet using Coinbase CDP or local key storage.
        """
        # --- 1. HANDLE CUSTOM CHAINS (e.g., Avalanche Fuji) ---
        if self.chain_id and self.rpc_url:
            return self._init_custom_evm()

        # --- 2. HANDLE CDP CLOUD CHAINS (e.g., Sepolia) ---
        return await self._init_cdp_evm()

    def _init_custom_evm(self) -> EthAccountWalletProvider:
        """
        Initializes a custom EVM wallet with local key storage.
        """
        str_chain_id = str(self.chain_id)
        logger.info(
            "Initializing custom EVM wallet for chain %s using data file: %s",
            str_chain_id,
            self.data_file,
        )

        # RUNTIME PATCH: Inject Avalanche Fuji into AgentKit's network maps
        CHAIN_ID_TO_NETWORK_ID[str_chain_id] = self.network_id

        # Clone an existing network layout structure as a placeholder to
        # pass internal checks.
        if "ethereum-sepolia" in NETWORK_ID_TO_CHAIN:
            NETWORK_ID_TO_CHAIN[self.network_id] = NETWORK_ID_TO_CHAIN[
                "ethereum-sepolia"
            ]
        elif "base-sepolia" in NETWORK_ID_TO_CHAIN:
            NETWORK_ID_TO_CHAIN[self.network_id] = NETWORK_ID_TO_CHAIN["base-sepolia"]
        else:
            NETWORK_ID_TO_CHAIN[self.network_id] = next(
                iter(NETWORK_ID_TO_CHAIN.values())
            )

        local_private_key = None
        if os.path.exists(self.data_file):
            try:
                with open(self.data_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    local_private_key = data.get("private_key")
            except Exception as e:  # pylint: disable=broad-exception-caught
                logger.warning(
                    "Failed to parse private key from local data file %s: %s",
                    self.data_file,
                    e,
                )

        # Create a local key if it doesn't exist yet
        if not local_private_key:
            logger.info(
                "Generating new local private key and saving to %s", self.data_file
            )
            new_account = Account.create()  # pylint: disable=no-value-for-parameter
            local_private_key = new_account.key.hex()
            with open(self.data_file, "w", encoding="utf-8") as f:
                json.dump({"private_key": local_private_key}, f)

        account = Account.from_key(local_private_key)  # pylint: disable=no-value-for-parameter

        config = EthAccountWalletProviderConfig(
            account=account,
            chain_id=str_chain_id,
            rpc_url=self.rpc_url,
        )
        provider = EthAccountWalletProvider(config)
        logger.info(
            "Successfully initialized custom EVM wallet for address: %s",
            provider.get_address(),
        )
        return provider

    async def _init_cdp_evm(self) -> CdpEvmWalletProvider:
        """
        Initializes an EVM wallet using Coinbase CDP.
        """
        logger.info("Initializing CDP EVM wallet for network: %s", self.network_id)
        key_file_path = os.getenv("CDP_API_KEY_FILE", "cdp_api_key.json")
        try:
            with open(key_file_path, "r", encoding="utf-8") as f:
                key_data = json.load(f)
                os.environ["CDP_API_KEY_ID"] = str(key_data.get("name", ""))
                os.environ["CDP_API_KEY_SECRET"] = str(
                    key_data.get("privateKey", "")
                ).replace("\\n", "\n")
        except FileNotFoundError:
            logger.debug(
                "CDP API key file %s not found. Relying on environment variables.",
                key_file_path,
            )

        wallet_address = None
        if os.path.exists(self.data_file):
            try:
                with open(self.data_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    wallet_address = data.get("address")
            except Exception as e:  # pylint: disable=broad-exception-caught
                logger.warning(
                    "Failed to parse wallet address from local data file %s: %s",
                    self.data_file,
                    e,
                )

        config = CdpEvmWalletProviderConfig(
            network_id=self.network_id,
        )

        if wallet_address:
            logger.info("Loading existing CDP wallet address: %s", wallet_address)
            config.address = wallet_address
        else:
            logger.info("Creating a new CDP wallet identifier")
            config.idempotency_key = str(uuid.uuid4())

        # CRITICAL FIX: The CdpEvmWalletProvider constructor calls asyncio.run()
        # internally. To avoid "RuntimeError: asyncio.run() cannot be called from
        # a running event loop", we must run the instantiation in a separate thread.
        loop = asyncio.get_running_loop()
        provider = await loop.run_in_executor(
            None, lambda: CdpEvmWalletProvider(config)
        )

        if wallet_address is None:
            wallet_address = provider.get_address()
            logger.info(
                "Persisting generated CDP wallet address %s to %s",
                wallet_address,
                self.data_file,
            )
            with open(self.data_file, "w", encoding="utf-8") as f:
                json.dump({"address": wallet_address}, f)

        logger.info(
            "Successfully initialized CDP EVM wallet for address: %s",
            wallet_address,
        )
        return provider

    async def get_balances(self) -> Dict[str, float]:
        """
        Fetches native and USDC balances for the EVM wallet.
        """
        try:
            native_balance = float(self.provider.get_balance() or 0.0) / 10**18
        except Exception as e:
            logger.warning(
                "Failed to fetch native balance for %s: %s", self.network_id, e
            )
            native_balance = 0.0

        usdc_balance = 0.0
        usdc_address = EVM_USDC_CONTRACTS.get(self.network_id)
        if usdc_address:
            try:
                balance_units = self.provider.read_contract(
                    contract_address=Web3.to_checksum_address(usdc_address),
                    abi=ERC20_ABI,
                    function_name="balanceOf",
                    args=[Web3.to_checksum_address(self.get_address())],
                )
                usdc_balance = float(balance_units) / 10**6
            except Exception as e:
                logger.warning(
                    "Failed to fetch USDC balance for %s: %s", self.network_id, e
                )

        return {"native": native_balance, "usdc": usdc_balance}

    def get_address(self) -> str:
        """Returns the address of the EVM wallet."""
        return str(self.provider.get_address())

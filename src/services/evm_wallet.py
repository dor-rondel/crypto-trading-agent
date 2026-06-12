"""
Service for managing EVM-specific wallet operations.
"""

import json
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


class EvmWallet:
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
        self.provider = self._init_evm()

    def _init_evm(self) -> Any:
        """
        Initializes an EVM wallet using Coinbase CDP or local key storage.
        """
        # --- 1. HANDLE CUSTOM CHAINS (e.g., Avalanche Fuji) ---
        if self.chain_id and self.rpc_url:
            return self._init_custom_evm()

        # --- 2. HANDLE CDP CLOUD CHAINS (e.g., Sepolia) ---
        return self._init_cdp_evm()

    def _init_custom_evm(self) -> EthAccountWalletProvider:
        """
        Initializes a custom EVM wallet with local key storage.
        """
        str_chain_id = str(self.chain_id)

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
            except Exception:  # pylint: disable=broad-exception-caught
                pass

        # Create a local key if it doesn't exist yet
        if not local_private_key:
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
        return EthAccountWalletProvider(config)

    def _init_cdp_evm(self) -> CdpEvmWalletProvider:
        """
        Initializes an EVM wallet using Coinbase CDP.
        """
        key_file_path = os.getenv("CDP_API_KEY_FILE", "cdp_api_key.json")
        try:
            with open(key_file_path, "r", encoding="utf-8") as f:
                key_data = json.load(f)
                os.environ["CDP_API_KEY_ID"] = str(key_data.get("name", ""))
                os.environ["CDP_API_KEY_SECRET"] = str(
                    key_data.get("privateKey", "")
                ).replace("\\n", "\n")
        except FileNotFoundError:
            pass

        wallet_address = None
        if os.path.exists(self.data_file):
            try:
                with open(self.data_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    wallet_address = data.get("address")
            except Exception:  # pylint: disable=broad-exception-caught
                pass

        config = CdpEvmWalletProviderConfig(
            network_id=self.network_id,
        )

        if wallet_address:
            config.address = wallet_address
        else:
            config.idempotency_key = str(uuid.uuid4())

        provider = CdpEvmWalletProvider(config)

        if wallet_address is None:
            with open(self.data_file, "w", encoding="utf-8") as f:
                json.dump({"address": provider.get_address()}, f)

        return provider

    def _save_wallet_secret(self, wallet_data: str) -> None:
        """Saves the wallet secret to the data file."""
        with open(self.data_file, "w", encoding="utf-8") as f:
            json.dump({"wallet_secret": wallet_data}, f)

    def get_balances(self) -> Dict[str, float]:
        """
        Fetches native balance for the EVM wallet.
        """
        try:
            native_balance = float(self.provider.get_balance() or 0.0) / 10**18
            return {"native": native_balance, "usdc": 0.0}
        except (ValueError, TypeError, RuntimeError):
            return {"native": 0.0, "usdc": 0.0}

    def get_address(self) -> str:
        """Returns the address of the EVM wallet."""
        return str(self.provider.get_address())

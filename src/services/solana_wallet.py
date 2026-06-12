"""
Service for managing Solana-specific wallet operations.
"""

import logging
import os
from typing import Dict

import base58
from solana.rpc.async_api import AsyncClient
from solana.rpc.types import TokenAccountOpts
from solders.keypair import Keypair  # type: ignore
from solders.pubkey import Pubkey

from src.services.base_wallet import BaseWallet

logger = logging.getLogger(__name__)

# Solana Devnet USDC Mint
SOLANA_USDC_MINT = "4zMMC9srt5Ri5X14GAgXhaHii3GnPAEERYPJgZJDncDU"


class SolanaWallet(BaseWallet):
    """
    Handles Solana Devnet wallet operations.
    """

    def __init__(self, rpc_url: str):
        """
        Initialize the Solana wallet and load the keypair.
        """
        self.rpc_url = rpc_url
        self.client = AsyncClient(self.rpc_url, timeout=60)
        self.keypair: Keypair = self._init_solana()

    def _init_solana(self) -> Keypair:
        """
        Initializes the Solana Devnet wallet.
        """
        logger.info("Initializing Solana wallet...")
        private_key_str = os.getenv("SOLANA_PRIVATE_KEY")
        wallet_file = ".solana_wallet"

        if private_key_str:
            try:
                keypair = Keypair.from_bytes(base58.b58decode(private_key_str))
                logger.info("Successfully loaded Solana keypair from environment.")
                return keypair
            except ValueError as e:
                logger.warning(
                    "Invalid SOLANA_PRIVATE_KEY format in env: %s. "
                    "Falling back to file persistence.",
                    e,
                )
                return self._load_or_create_solana_file(wallet_file)

        return self._load_or_create_solana_file(wallet_file)

    def _load_or_create_solana_file(self, file_path: str) -> Keypair:
        """
        Loads a Solana keypair from a file or creates a new one.
        """
        if os.path.exists(file_path):
            try:
                with open(file_path, "rb") as f:
                    keypair = Keypair.from_bytes(f.read())
                logger.info(
                    "Successfully loaded Solana keypair from file: %s", file_path
                )
                return keypair
            except Exception as e:
                logger.warning(
                    "Failed to read Solana keypair file %s: %s. Creating a new one.",
                    file_path,
                    e,
                )

        logger.info("Generating a new Solana keypair and saving to %s", file_path)
        keypair = Keypair()
        try:
            with open(file_path, "wb") as f:
                f.write(bytes(keypair))
        except Exception as e:
            logger.error("Failed to write new keypair to %s: %s", file_path, e)

        return keypair

    async def get_balances(self) -> Dict[str, float]:
        """
        Fetches balances using the async client.
        """
        sol_balance = 0.0
        usdc_balance = 0.0
        pubkey = self.keypair.pubkey()

        try:
            # Native Balance
            res = await self.client.get_balance(pubkey)
            sol_balance = res.value / 10**9

            # USDC Balance
            usdc_pubkey = Pubkey.from_string(SOLANA_USDC_MINT)
            token_res = await self.client.get_token_accounts_by_owner(
                pubkey, TokenAccountOpts(mint=usdc_pubkey)
            )

            if token_res.value:
                account_pubkey = token_res.value[0].pubkey
                balance_res = await self.client.get_token_account_balance(
                    account_pubkey
                )
                if balance_res.value and balance_res.value.ui_amount:
                    usdc_balance = float(balance_res.value.ui_amount)

        except Exception as e:
            logger.warning("Failed to fetch Solana balances: %s", e)

        return {"native": sol_balance, "usdc": usdc_balance}

    def get_address(self) -> str:
        """Returns the public address."""
        return str(self.keypair.pubkey())

    def get_private_key_b58(self) -> str:
        """Returns the base58 encoded private key."""
        return base58.b58encode(bytes(self.keypair)).decode()

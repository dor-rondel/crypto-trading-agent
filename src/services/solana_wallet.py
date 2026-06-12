"""
Service for managing Solana-specific wallet operations.
"""

import logging
import os
from typing import Dict

import base58
from solana.rpc.api import Client
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

    def __init__(self, client: Client):
        self.client = client
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
                logger.info(
                    "Successfully loaded Solana keypair from environment variable."
                )
                return keypair
            except ValueError as e:
                logger.warning(
                    "Invalid SOLANA_PRIVATE_KEY format in environment variables: %s. "
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

    def get_balances(self) -> Dict[str, float]:
        """
        Fetches native and USDC balances for Solana.
        """
        try:
            # Native Balance
            sol_balance = self.client.get_balance(self.keypair.pubkey()).value / 10**9
        except Exception as e:
            logger.warning("Failed to fetch Solana native balance: %s", e)
            sol_balance = 0.0

        usdc_balance = 0.0
        try:
            # USDC Balance
            usdc_pubkey = Pubkey.from_string(SOLANA_USDC_MINT)
            token_accounts = self.client.get_token_accounts_by_owner(
                self.keypair.pubkey(), TokenAccountOpts(mint=usdc_pubkey)
            )

            if token_accounts.value:
                account_pubkey = token_accounts.value[0].pubkey
                account_info = self.client.get_token_account_balance(account_pubkey)
                if account_info.value and account_info.value.ui_amount:
                    usdc_balance = float(account_info.value.ui_amount)
        except Exception as e:
            logger.warning("Failed to fetch Solana USDC balance: %s", e)

        return {"native": sol_balance, "usdc": usdc_balance}

    def get_address(self) -> str:
        """Returns the public address."""
        return str(self.keypair.pubkey())

    def get_private_key_b58(self) -> str:
        """Returns the base58 encoded private key."""
        return base58.b58encode(bytes(self.keypair)).decode()

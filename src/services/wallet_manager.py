"""
Orchestrator for managing multi-chain wallets.
"""

import logging
from typing import Dict

from src.config import Config
from src.services.base_wallet import BaseWallet
from src.services.evm_wallet import EvmWallet
from src.services.solana_wallet import SolanaWallet

logger = logging.getLogger(__name__)


class WalletManager:
    """
    Orchestrates wallet lifecycle across supported chains.
    """

    def __init__(self) -> None:
        """
        Initialize the WalletManager container.
        """
        logger.info("Initializing WalletManager container...")
        self.wallets: Dict[str, BaseWallet] = {}

    async def initialize(self) -> None:
        """
        Asynchronously load/create wallets for all chains.
        """
        logger.info("Asynchronously loading wallets for all chains...")

        # Instantiate wallets
        self.wallets = {
            "solana": SolanaWallet(Config.SOLANA_RPC_URL),
            "sepolia": EvmWallet(
                "ethereum-sepolia",
                Config.SEPOLIA_WALLET_DATA_FILE,
            ),
            "avalanche-fuji": EvmWallet(
                "avalanche-fuji",
                Config.FUJI_WALLET_DATA_FILE,
                chain_id="43113",
                rpc_url=Config.AVAX_FUJI_RPC_URL,
            ),
        }

        # Async initialization for each wallet
        for network_id, wallet in self.wallets.items():
            if network_id != "solana" and hasattr(wallet, "initialize"):
                logger.info("Initializing wallet for network: %s", network_id)
                await wallet.initialize()  # type: ignore

        logger.info("All wallets successfully loaded.")
        self._write_wallet_info_file()

    def get_address(self, network_id: str) -> str:
        """
        Returns the address of a wallet for a given network.
        """
        wallet = self.wallets.get(network_id)
        if not wallet:
            logger.error("Requested wallet address for unknown network: %s", network_id)
            return "ERROR"
        return wallet.get_address()

    def _write_wallet_info_file(self) -> None:
        """
        Writes public wallet information and funding instructions to WALLETS.md.
        """
        logger.info("Writing WALLETS.md wallet information file...")
        info = "# Wallet Information & Funding Instructions\n\n"
        info += "Use the following to fund wallets\n"
        info += "with testnet Native tokens and USDC.\n\n"

        # Solana
        sol = self.wallets.get("solana")
        info += "### Solana Devnet\n"
        if isinstance(sol, SolanaWallet):
            info += f"- **Address:** `{sol.get_address()}`\n"
            info += f"- **Private Key:** `{sol.get_private_key_b58()}`\n"
        else:
            info += "- **Address:** `ERROR`\n"
            info += "- **Private Key:** `ERROR`\n"
        info += "- **Faucet:** [Solana Faucet](https://faucet.solana.com/)\n\n"

        # EVM
        for network in ["sepolia", "avalanche-fuji"]:
            wallet = self.wallets.get(network)
            info += f"### {network.capitalize()}\n"
            addr = wallet.get_address() if isinstance(wallet, EvmWallet) else "ERROR"
            info += f"- **Address:** `{addr}`\n"
            info += "- **Faucet:** [Coinbase Faucet]"
            info += "(https://www.coinbase.com/faucets)\n\n"

        info += "---\n"
        info += "*Note: Private keys are included here for testnet convenience.*\n"

        try:
            with open("WALLETS.md", "w", encoding="utf-8") as f:
                f.write(info)
            logger.info("WALLETS.md successfully written.")
        except Exception as e:
            logger.error("Failed to write WALLETS.md: %s", e)

    async def get_balances(self) -> Dict[str, Dict[str, float]]:
        """
        Fetches balances for all wallets asynchronously.
        """
        results: Dict[str, Dict[str, float]] = {}
        for name, wallet in self.wallets.items():
            results[name] = await wallet.get_balances()
        return results

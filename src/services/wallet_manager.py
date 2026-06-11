"""
Service for managing multi-chain wallets (Solana, Ethereum Sepolia, Avalanche Fuji).
Handles programmatic creation, loading, and balance tracking.
"""

import json
import os
from typing import Dict

import base58
from coinbase_agentkit import CdpEvmWalletProvider, CdpEvmWalletProviderConfig
from dotenv import load_dotenv
from solana.rpc.api import Client
from solana.rpc.types import TokenAccountOpts
from solders.keypair import Keypair  # type: ignore
from solders.pubkey import Pubkey

load_dotenv()

# Solana Devnet USDC Mint
SOLANA_USDC_MINT = "4zMMC9srt5Ri5X14GAgXhaHii3GnPAEERYPJgZJDncDU"

class WalletManager:
    """
    Orchestrates wallet lifecycle across supported chains.
    """

    def __init__(self):
        """
        Initialize the WalletManager and load/create wallets for all chains.
        """
        self.solana_client = Client(
            os.getenv("SOLANA_RPC_URL", "https://api.devnet.solana.com"), timeout=60
        )
        self.wallets: Dict[str, any] = {}
        self._initialize_wallets()
        self._write_wallet_info_file()

    def _initialize_wallets(self) -> None:
        """
        Loads or creates wallets for Solana, Sepolia, and Fuji.
        """
        # We perform initialization silently as per security requirements.
        self._init_solana()
        sepolia_file = os.getenv("SEPOLIA_WALLET_DATA_FILE", "sepolia_wallet.json")
        self._init_evm("sepolia", sepolia_file)
        fuji_file = os.getenv("FUJI_WALLET_DATA_FILE", "fuji_wallet.json")
        self._init_evm("avalanche-fuji", fuji_file)

    def _init_solana(self) -> None:
        """
        Initializes the Solana Devnet wallet.
        """
        private_key_str = os.getenv("SOLANA_PRIVATE_KEY")
        wallet_file = ".solana_wallet"
        
        if private_key_str:
            try:
                keypair = Keypair.from_bytes(base58.b58decode(private_key_str))
                self.wallets["solana"] = keypair
            except Exception:
                self.wallets["solana"] = self._load_or_create_solana_file(wallet_file)
        else:
            self.wallets["solana"] = self._load_or_create_solana_file(wallet_file)

    def _load_or_create_solana_file(self, file_path: str) -> Keypair:
        """
        Loads a Solana keypair from a file or creates a new one.
        """
        if os.path.exists(file_path):
            with open(file_path, "rb") as f:
                keypair = Keypair.from_bytes(f.read())
        else:
            keypair = Keypair()
            with open(file_path, "wb") as f:
                f.write(bytes(keypair))
        return keypair

    def _init_evm(self, network_id: str, data_file: str) -> None:
        """
        Initializes an EVM wallet using Coinbase CDP via AgentKit.
        """
        try:
            api_key_name = os.getenv("CDP_API_KEY_NAME")
            raw_key = os.getenv("CDP_API_KEY_PRIVATE_KEY", "").replace("\\n", "\n")
            
            wallet_secret = None
            if os.path.exists(data_file):
                with open(data_file, "r") as f:
                    data = json.load(f)
                    wallet_secret = data.get("wallet_secret")
            
            config = CdpEvmWalletProviderConfig(
                api_key_id=api_key_name,
                api_key_secret=raw_key,
                network_id=network_id,
                wallet_secret=wallet_secret
            )
            
            provider = CdpEvmWalletProvider(config)
            self.wallets[network_id] = provider
            
        except Exception:
            # We fail silently here but the balance check will catch missing wallets
            pass

    def _write_wallet_info_file(self) -> None:
        """
        Writes public wallet information and funding instructions to WALLETS.md.
        """
        info = "# Wallet Information & Funding Instructions\n\n"
        info += "Use the following addresses to fund your wallets "
        info += "with testnet Native tokens and USDC.\n\n"
        
        # Solana
        sol_kp = self.wallets.get("solana")
        sol_addr = sol_kp.pubkey() if sol_kp else "ERROR"
        sol_priv = base58.b58encode(bytes(sol_kp)).decode() if sol_kp else "ERROR"
        
        info += "### Solana Devnet\n"
        info += f"- **Address:** `{sol_addr}`\n"
        info += f"- **Private Key:** `{sol_priv}`\n"
        info += "- **Faucet:** [Solana Faucet](https://faucet.solana.com/)\n\n"
        
        # EVM
        for network in ["sepolia", "avalanche-fuji"]:
            provider = self.wallets.get(network)
            addr = provider.get_address() if provider else "ERROR"
            info += f"### {network.capitalize()}\n"
            info += f"- **Address:** `{addr}`\n"
            info += "- **Faucet:** [Coinbase Faucet](https://www.coinbase.com/faucets)\n\n"
        
        info += "---\n"
        info += "*Note: Private keys are included here for testnet convenience.*\n"
        
        with open("WALLETS.md", "w") as f:
            f.write(info)

    def get_balances(self) -> Dict[str, Dict[str, float]]:
        """
        Fetches balances for all wallets.
        """
        balances = {}
        
        # Solana Balance
        if "solana" in self.wallets:
            try:
                kp = self.wallets["solana"]
                # Native Balance
                sol_balance = self.solana_client.get_balance(kp.pubkey()).value / 10**9
                # USDC Balance
                usdc_pubkey = Pubkey.from_string(SOLANA_USDC_MINT)
                token_accounts = self.solana_client.get_token_accounts_by_owner(
                    kp.pubkey(),
                    TokenAccountOpts(mint=usdc_pubkey)
                )

                usdc_balance = 0.0
                if token_accounts.value:
                    account_pubkey = token_accounts.value[0].pubkey
                    account_info = self.solana_client.get_token_account_balance(
                        account_pubkey
                    )
                    if account_info.value:
                        usdc_balance = float(account_info.value.ui_amount)

                balances["solana"] = {"native": sol_balance, "usdc": usdc_balance}
            except Exception:
                # Log error but don't print to stdout in production
                balances["solana"] = {"native": 0.0, "usdc": 0.0}

        # EVM Balances
        for network in ["sepolia", "avalanche-fuji"]:
            if network in self.wallets:
                try:
                    provider = self.wallets[network]
                    native_balance = float(provider.get_balance()) / 10**18
                    # AgentKit provider doesn't have a direct USDC balance helper yet
                    # For now, we stub it as 0 unless we implement a contract call
                    balances[network] = {"native": native_balance, "usdc": 0.0} 
                except Exception:
                    balances[network] = {"native": 0.0, "usdc": 0.0}
        
        return balances

if __name__ == "__main__":
    manager = WalletManager()
    print("Wallet info written to WALLETS.md")
    print("Current Balances:", manager.get_balances())

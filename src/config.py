"""
Configuration management for the crypto-trading-agent.
"""

import os

from dotenv import load_dotenv

load_dotenv()


class Config:
    """
    Centralized configuration management using environment variables.
    """

    SOLANA_RPC_URL = os.getenv("SOLANA_RPC_URL", "https://api.devnet.solana.com")
    SEPOLIA_WALLET_DATA_FILE = os.getenv(
        "SEPOLIA_WALLET_DATA_FILE", "sepolia_wallet.json"
    )
    FUJI_WALLET_DATA_FILE = os.getenv("FUJI_WALLET_DATA_FILE", "fuji_wallet.json")
    AVAX_FUJI_RPC_URL = os.getenv("AVAX_FUJI_RPC_URL")

"""
Integration test script for verifying swaps on Solana Devnet and EVM Testnets.
Usage: uv run scripts/test_swaps.py --chain solana --direction buy ...
"""

import argparse
import asyncio
import logging
import os
import sys

# Add src to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.services.wallet_manager import WalletManager

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def main():
    parser = argparse.ArgumentParser(description="Test swaps on various chains.")
    parser.add_argument(
        "--chain",
        choices=["solana", "sepolia", "avalanche-fuji"],
        required=True,
        help="The chain to test on.",
    )
    parser.add_argument(
        "--direction",
        choices=["buy", "sell"],
        required=True,
        help="Swap direction.",
    )
    parser.add_argument(
        "--amount",
        type=float,
        required=True,
        help="Amount to swap (USDC if buy, Asset if sell).",
    )
    parser.add_argument(
        "--asset",
        required=True,
        help="Target asset symbol (e.g., SOL, ETH, AVAX).",
    )

    args = parser.parse_args()

    wm = WalletManager()
    await wm.initialize()

    try:
        logger.info(
            "Starting test swap: %s %s %s on %s",
            args.direction.upper(),
            args.amount,
            args.asset,
            args.chain,
        )
        tx_hash = await wm.execute_swap(
            args.chain, args.direction, args.amount, args.asset
        )
        logger.info("Swap successful! Transaction Hash: %s", tx_hash)
        logger.info("View on explorer:")
        if args.chain == "solana":
            logger.info(
                "https://explorer.solana.com/tx/%s?cluster=devnet",
                tx_hash.replace("solana-tx-", ""),
            )
        elif args.chain == "sepolia":
            logger.info("https://sepolia.etherscan.io/tx/%s", tx_hash.split("-")[-1])
        elif args.chain == "avalanche-fuji":
            logger.info("https://testnet.snowtrace.io/tx/%s", tx_hash.split("-")[-1])

    except Exception as e:
        logger.error("Swap failed: %s", e)


if __name__ == "__main__":
    asyncio.run(main())

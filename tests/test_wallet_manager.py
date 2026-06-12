from unittest.mock import MagicMock, mock_open, patch

import pytest

from src.services.evm_wallet import EvmWallet
from src.services.solana_wallet import SolanaWallet
from src.services.wallet_manager import WalletManager


@pytest.fixture
async def manager():
    # Prevent file writing and initialization side effects
    with (
        patch("src.services.wallet_manager.WalletManager._write_wallet_info_file"),
        patch("src.services.wallet_manager.SolanaWallet"),
        patch("src.services.wallet_manager.EvmWallet"),
    ):
        manager = WalletManager()
        # Setup dummy wallets
        mock_solana = MagicMock(spec=SolanaWallet)
        mock_evm = MagicMock(spec=EvmWallet)
        manager.wallets = {
            "solana": mock_solana,
            "sepolia": mock_evm,
            "avalanche-fuji": mock_evm,
        }
        return manager


@pytest.mark.asyncio
async def test_get_address(manager):
    manager.wallets["solana"].get_address.return_value = "sol_addr"
    assert manager.get_address("solana") == "sol_addr"
    assert manager.get_address("invalid") == "ERROR"


@pytest.mark.asyncio
async def test_write_wallet_info_file():
    # Setup a minimal manager without calling its real __init__ which is complex to mock
    with patch("src.services.wallet_manager.WalletManager.__init__", return_value=None):
        manager = WalletManager()
        manager.wallets = {}

        # Setup mock wallets
        mock_sol = MagicMock(spec=SolanaWallet)
        mock_sol.get_address.return_value = "sol_addr"
        mock_sol.get_private_key_b58.return_value = "sol_pk"
        manager.wallets["solana"] = mock_sol

        mock_evm = MagicMock(spec=EvmWallet)
        mock_evm.get_address.return_value = "evm_addr"
        manager.wallets["sepolia"] = mock_evm
        manager.wallets["avalanche-fuji"] = mock_evm

        # Call the real method and verify file opened
        with patch("builtins.open", mock_open()) as m_write:
            manager._write_wallet_info_file()
            # Verify file opened
            m_write.assert_called_with("WALLETS.md", "w", encoding="utf-8")
            # Verify some expected content was written
            handle = m_write()
            # Concatenate all write calls to check for content
            written_content = "".join(
                call.args[0] for call in handle.write.call_args_list
            )
            assert "sol_addr" in written_content
            assert "evm_addr" in written_content

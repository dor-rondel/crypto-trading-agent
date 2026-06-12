import unittest
from unittest.mock import MagicMock, mock_open, patch

from src.services.evm_wallet import EvmWallet
from src.services.solana_wallet import SolanaWallet
from src.services.wallet_manager import WalletManager


class TestWalletManager(unittest.TestCase):
    @patch("src.services.wallet_manager.SolanaWallet")
    @patch("src.services.wallet_manager.EvmWallet")
    @patch("src.services.wallet_manager.Client")
    def setUp(self, mock_client, mock_evm, mock_solana):
        # Prevent file writing during initialization
        with patch("src.services.wallet_manager.WalletManager._write_wallet_info_file"):
            self.manager = WalletManager()
            # Setup dummy wallets
            self.manager.wallets = {
                "solana": mock_solana(),
                "sepolia": mock_evm(),
                "avalanche-fuji": mock_evm(),
            }

    def test_get_address(self):
        self.manager.wallets["solana"].get_address.return_value = "sol_addr"
        self.assertEqual(self.manager.get_address("solana"), "sol_addr")
        self.assertEqual(self.manager.get_address("invalid"), "ERROR")

    @patch("src.services.wallet_manager.Client")
    def test_write_wallet_info_file(self, mock_client):
        # Prevent initialization side effects by patching open during setup
        # Return empty JSON object to satisfy EvmWallet initialization
        m_open = mock_open(read_data="{}")

        # Need a mock provider that returns a string address
        mock_cdp = MagicMock()
        mock_cdp.get_address.return_value = "mock_addr"

        with (
            patch("builtins.open", m_open),
            patch(
                "src.services.evm_wallet.CdpEvmWalletProvider",
                return_value=mock_cdp,
            ),
        ):
            manager = WalletManager()

            # Setup mock wallets (instances of real classes)
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


if __name__ == "__main__":
    unittest.main()

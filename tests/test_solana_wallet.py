import unittest
from unittest.mock import MagicMock, mock_open, patch

from solana.rpc.api import Client
from solders.pubkey import Pubkey

from src.services.solana_wallet import SolanaWallet


class TestSolanaWallet(unittest.TestCase):
    def setUp(self):
        self.client = MagicMock(spec=Client)

    @patch("os.getenv")
    @patch("os.path.exists")
    @patch("builtins.open", new_callable=mock_open, read_data=b"mocked_keypair_bytes")
    @patch("solders.keypair.Keypair.from_bytes")
    def test_init_with_file(
        self, mock_from_bytes, mock_open_file, mock_exists, mock_getenv
    ):
        mock_getenv.return_value = None
        mock_exists.return_value = True

        wallet = SolanaWallet(self.client)

        self.assertTrue(mock_exists.called)
        self.assertEqual(wallet.client, self.client)

    def test_get_address(self):
        with patch("src.services.solana_wallet.Keypair"):
            wallet = SolanaWallet(self.client)
            # Use a valid length base58 string for a pubkey
            pubkey_str = "11111111111111111111111111111111"
            wallet.keypair.pubkey.return_value = Pubkey.from_string(pubkey_str)
            self.assertEqual(wallet.get_address(), pubkey_str)

    def test_get_balances_success(self):
        with patch("src.services.solana_wallet.Keypair"):
            wallet = SolanaWallet(self.client)
            wallet.keypair.pubkey.return_value = Pubkey.from_string(
                "11111111111111111111111111111111"
            )

            # Mock SOL balance
            self.client.get_balance.return_value.value = 1_000_000_000  # 1 SOL

            # Mock USDC account - use a valid length pubkey
            mock_token_account = MagicMock()
            mock_token_account.pubkey = Pubkey.from_string(
                "11111111111111111111111111111111"
            )
            self.client.get_token_accounts_by_owner.return_value.value = [
                mock_token_account
            ]
            self.client.get_token_account_balance.return_value.value.ui_amount = 100.0

            balances = wallet.get_balances()
            self.assertEqual(balances["native"], 1.0)
            self.assertEqual(balances["usdc"], 100.0)

    def test_get_balances_network_failure(self):
        # Mock native balance failure
        self.client.get_balance.side_effect = Exception("Network down")

        # Also mock token accounts call to avoid it proceeding/using previous state
        self.client.get_token_accounts_by_owner.side_effect = Exception("Network down")

        wallet = SolanaWallet(self.client)
        balances = wallet.get_balances()
        self.assertEqual(balances["native"], 0.0)
        self.assertEqual(balances["usdc"], 0.0)


if __name__ == "__main__":
    unittest.main()

import unittest
from unittest.mock import mock_open, patch

from src.services.evm_wallet import EvmWallet


class TestEvmWallet(unittest.TestCase):
    @patch("src.services.evm_wallet.CdpEvmWalletProvider")
    @patch("src.services.evm_wallet.os.path.exists")
    @patch("src.services.evm_wallet.os.getenv")
    def setUp(self, mock_getenv, mock_exists, mock_provider):
        mock_exists.return_value = False
        mock_getenv.return_value = "mock_api_key_file.json"

        # Mock the provider's address
        mock_provider.return_value.get_address.return_value = "0x123"

        with patch(
            "builtins.open", mock_open(read_data='{"name": "a", "privateKey": "b"}')
        ):
            self.wallet = EvmWallet("ethereum-sepolia", "sepolia_wallet.json")
            self.provider = self.wallet.provider

    def test_get_address(self):
        self.assertEqual(self.wallet.get_address(), "0x123")

    def test_get_balances_success(self):
        self.provider.get_balance.return_value = 1 * 10**18  # 1 ETH
        self.provider.read_contract.return_value = 100 * 10**6  # 100 USDC

        # Patch Web3.to_checksum_address to just return the input
        with patch(
            "src.services.evm_wallet.Web3.to_checksum_address", side_effect=lambda x: x
        ):
            balances = self.wallet.get_balances()
            self.assertEqual(balances["native"], 1.0)
            self.assertEqual(balances["usdc"], 100.0)

    def test_get_balances_contract_failure(self):
        self.provider.get_balance.return_value = 1 * 10**18  # 1 ETH
        self.provider.read_contract.side_effect = Exception("Contract call failed")

        balances = self.wallet.get_balances()
        self.assertEqual(balances["native"], 1.0)
        self.assertEqual(balances["usdc"], 0.0)

    @patch("src.services.evm_wallet.EthAccountWalletProvider")
    def test_init_custom_evm(self, mock_provider_class):
        # Setup for custom chain
        with (
            patch("src.services.evm_wallet.os.path.exists", return_value=False),
            patch("builtins.open", mock_open()),
        ):
            wallet = EvmWallet(
                "custom-chain",
                "custom_wallet.json",
                chain_id="123",
                rpc_url="http://mock.rpc",
            )
            self.assertTrue(mock_provider_class.called)
            self.assertEqual(wallet.chain_id, "123")


if __name__ == "__main__":
    unittest.main()

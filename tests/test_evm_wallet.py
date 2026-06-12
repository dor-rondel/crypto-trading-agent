from unittest.mock import MagicMock, mock_open, patch

import pytest

from src.services.evm_wallet import EvmWallet


@pytest.fixture
async def mock_wallet():
    with (
        patch("src.services.evm_wallet.CdpEvmWalletProvider") as mock_provider_class,
        patch("src.services.evm_wallet.os.path.exists", return_value=False),
        patch(
            "src.services.evm_wallet.os.getenv", return_value="mock_api_key_file.json"
        ),
        patch("builtins.open", mock_open(read_data='{"name": "a", "privateKey": "b"}')),
    ):
        mock_provider = MagicMock()
        mock_provider.get_address.return_value = "0x123"
        # Since we use run_in_executor, we need to mock the constructor return
        mock_provider_class.return_value = mock_provider

        wallet = EvmWallet("ethereum-sepolia", "sepolia_wallet.json")
        await wallet.initialize()
        return wallet


@pytest.mark.asyncio
async def test_get_address(mock_wallet):
    assert mock_wallet.get_address() == "0x123"


@pytest.mark.asyncio
async def test_get_balances_success(mock_wallet):
    mock_wallet.provider.get_balance.return_value = 1 * 10**18  # 1 ETH
    mock_wallet.provider.read_contract.return_value = 100 * 10**6  # 100 USDC

    # Patch Web3.to_checksum_address to just return the input
    with patch(
        "src.services.evm_wallet.Web3.to_checksum_address", side_effect=lambda x: x
    ):
        balances = await mock_wallet.get_balances()
        assert balances["native"] == 1.0
        assert balances["usdc"] == 100.0


@pytest.mark.asyncio
async def test_get_balances_contract_failure(mock_wallet):
    mock_wallet.provider.get_balance.return_value = 1 * 10**18  # 1 ETH
    mock_wallet.provider.read_contract.side_effect = Exception("Contract call failed")

    balances = await mock_wallet.get_balances()
    assert balances["native"] == 1.0
    assert balances["usdc"] == 0.0


@pytest.mark.asyncio
@patch("src.services.evm_wallet.EthAccountWalletProvider")
async def test_init_custom_evm(mock_provider_class):
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
        await wallet.initialize()
        assert mock_provider_class.called
        assert wallet.chain_id == "123"

from unittest.mock import AsyncMock, MagicMock, mock_open, patch

import pytest
from solders.pubkey import Pubkey

from src.services.solana_wallet import SolanaWallet


@pytest.fixture
def rpc_url():
    return "https://api.devnet.solana.com"


@pytest.mark.asyncio
@patch("os.getenv")
@patch("os.path.exists")
@patch("builtins.open", new_callable=mock_open, read_data=b"mocked_keypair_bytes")
@patch("solders.keypair.Keypair.from_bytes")
async def test_init_with_file(
    mock_from_bytes, mock_open_file, mock_exists, mock_getenv, rpc_url
):
    mock_getenv.return_value = None
    mock_exists.return_value = True

    # Constructor is now synchronous again
    wallet = SolanaWallet(rpc_url)

    assert mock_exists.called
    assert wallet.rpc_url == rpc_url


@pytest.mark.asyncio
async def test_get_address(rpc_url):
    with patch("src.services.solana_wallet.Keypair"):
        wallet = SolanaWallet(rpc_url)
        # Use a valid length base58 string for a pubkey
        pubkey_str = "11111111111111111111111111111111"
        wallet.keypair.pubkey.return_value = Pubkey.from_string(pubkey_str)
        assert wallet.get_address() == pubkey_str


@pytest.mark.asyncio
async def test_get_balances_success(rpc_url):
    with (
        patch("src.services.solana_wallet.Keypair"),
        patch("src.services.solana_wallet.AsyncClient") as mock_client_class,
    ):
        mock_client = mock_client_class.return_value
        wallet = SolanaWallet(rpc_url)
        wallet.keypair.pubkey.return_value = Pubkey.from_string(
            "11111111111111111111111111111111"
        )

        # Mock SOL balance
        mock_client.get_balance = AsyncMock()
        mock_client.get_balance.return_value.value = 1_000_000_000  # 1 SOL

        # Mock USDC account
        mock_token_account = MagicMock()
        mock_token_account.pubkey = Pubkey.from_string(
            "11111111111111111111111111111111"
        )
        mock_client.get_token_accounts_by_owner = AsyncMock()
        mock_client.get_token_accounts_by_owner.return_value.value = [
            mock_token_account
        ]

        mock_client.get_token_account_balance = AsyncMock()
        mock_client.get_token_account_balance.return_value.value.ui_amount = 100.0

        balances = await wallet.get_balances()
        assert balances["native"] == 1.0
        assert balances["usdc"] == 100.0

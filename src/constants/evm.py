"""
Constants for EVM-based chains (Ethereum Sepolia, Avalanche Fuji).
"""

# Standard testnet USDC contract addresses
USDC_CONTRACTS = {
    "ethereum-sepolia": "0x1c7D4B196Cb0C7B01d743Fbc6116a902379C7238",
    "avalanche-fuji": "0x5425890298aed601595a70AB815c96711a31Bc65",
}

# Uniswap V3 Router Addresses
# Sepolia: Official Uniswap Labs deployment
# Fuji: Community deployment (SwapRouter)
ROUTER_ADDRESSES = {
    "ethereum-sepolia": "0x3bFA4769FB09eefC5a80d6E87c3B9C650f7Ae48E",
    "avalanche-fuji": "0xA4DCf4082A2270e95BB60Db0C5Ff4BBB63e29178",
}

# Native Wrapper addresses (required for Uniswap V3 ERC-20 compatibility)
NATIVE_WRAPPERS = {
    "ethereum-sepolia": "0x7b79995e5f793A07Bc00c21412e50Ecae098E7f9",  # WETH
    "avalanche-fuji": "0xd00ae08403B9bbb9124bB305C09058E32C39A48c",  # WAVAX
}

# Minimal ERC20 ABI
ERC20_ABI = [
    {
        "constant": True,
        "inputs": [{"name": "_owner", "type": "address"}],
        "name": "balanceOf",
        "outputs": [{"name": "balance", "type": "uint256"}],
        "type": "function",
    },
    {
        "constant": False,
        "inputs": [
            {"name": "_spender", "type": "address"},
            {"name": "_value", "type": "uint256"},
        ],
        "name": "approve",
        "outputs": [{"name": "success", "type": "bool"}],
        "type": "function",
    },
]

# Minimal Uniswap V3 SwapRouter ABI
ROUTER_ABI = [
    {
        "inputs": [
            {
                "components": [
                    {"internalType": "address", "name": "tokenIn", "type": "address"},
                    {"internalType": "address", "name": "tokenOut", "type": "address"},
                    {"internalType": "uint24", "name": "fee", "type": "uint24"},
                    {"internalType": "address", "name": "recipient", "type": "address"},
                    {"internalType": "uint256", "name": "deadline", "type": "uint256"},
                    {"internalType": "uint256", "name": "amountIn", "type": "uint256"},
                    {
                        "internalType": "uint256",
                        "name": "amountOutMinimum",
                        "type": "uint256",
                    },
                    {
                        "internalType": "uint160",
                        "name": "sqrtPriceLimitX96",
                        "type": "uint160",
                    },
                ],
                "internalType": "struct ISwapRouter.ExactInputSingleParams",
                "name": "params",
                "type": "tuple",
            }
        ],
        "name": "exactInputSingle",
        "outputs": [
            {"internalType": "uint256", "name": "amountOut", "type": "uint256"}
        ],
        "stateMutability": "payable",
        "type": "function",
    }
]

# Agentic Testnet Trading System

## Overview

This project is an event-driven, agentic cryptocurrency trading simulation platform built for test networks.

The system executes simulated trading strategies against:

- **Solana Devnet** (via `solana-py`)
- **Ethereum Sepolia** (via `AgentKit/CDP`)
- **Avalanche Fuji** (via `AgentKit/CDP`)

Real market data is used to generate trading signals, while all trade execution occurs on testnets using a **three-wallet USDC strategy** to avoid risking real capital.

---

## Goals

- Evaluate AI-generated trading strategies safely
- Simulate multi-chain portfolio management
- Test autonomous trading workflows
- Support long-running blockchain operations
- Maintain reproducibility and auditability

---

## Core Technologies

### AI / Workflow

- LangGraph
- LangChain
- **Groq** (via LangChain-Groq)
- **LangSmith** (for observability)
- **Coinbase AgentKit** (for EVM execution)

### Blockchain

- **Solana Python SDK** (`solana-py`)
- **Coinbase CDP SDK**
- **web3.py** (for deterministic validations)

### Infrastructure

- Python 3.12+
- PostgreSQL (for workflow persistence)

---

## Architecture

### High-Level Flow

Market Watcher → Signal Generated → Planner Agent → Structured Plan → Validator → Executor → Transaction Monitor → Portfolio Manager

---

## Design Principles

### Plan First, Execute Second
Agents generate structured plans using **Pydantic** models. Executors are responsible for carrying out these plans deterministically.

### Event-Driven Workflows
Workflows are state machines resumed by events (e.g., `TX_CONFIRMED`, `MARKET_SIGNAL`). They persist state and do not remain active while waiting.

### Unified Wallet Interface
All multi-chain wallets inherit from the `BaseWallet` abstract class. This guarantees that every wallet implements identical interfaces for retrieving public addresses (`get_address() -> str`) and balances (`get_balances() -> Dict[str, float]`). The `WalletManager` acts as the orchestrator and holds strongly typed mappings of network IDs to these `BaseWallet` instances.

### Deterministic Services
The Wallet Manager, Chain Adapters, and Portfolio Manager must remain deterministic and free of LLM reasoning.

### Three-Wallet USDC Strategy
The system maintains a USDC "bank" on each supported chain. All trades are simulated by swapping USDC for assets and back, ensuring a consistent base currency for performance tracking. Solana balances are fetched from the devnet token account, and EVM balances are queried programmatically from the official Sepolia and Avalanche Fuji USDC token contract addresses using `read_contract` calls.

### Initialization & Funding
Upon first run, the system creates necessary wallets and generates a `WALLETS.md` file (ignored by git). This file contains public addresses, private keys (for testnet convenience), and faucet links. The system will poll for balances and wait until at least one wallet is funded before proceeding.

### Subsequent Runs & Persistence
The system automatically loads existing wallets from `.solana_wallet`, `sepolia_wallet.json`, and `fuji_wallet.json` if they exist in the root directory.
*   **Do not** rely on environment variables (`SOLANA_PRIVATE_KEY`) after initial setup, as they are only used for bootstrapping.
*   Check `WALLETS.md` for addresses if you need to re-fund.

---

## Development

### Prerequisites

- Python 3.12+
- [uv](https://github.com/astral-sh/uv)
- `libffi-dev` (required for `cffi` build)

### Install

```bash
# Install dependencies and setup virtual environment
make install
```

### Run Quality Checks

```bash
# Run comprehensive format check, ruff check, pylint, mypy, pytest, and codespell
make check

# Or run just formatting or linter checks individually
make format
make lint
```

### Run Tests

```bash
# Run pytest
make test
```

### Configuration

Ensure your `.env` file is configured with the necessary API keys and RPC URLs (especially for reliable Solana Devnet connectivity).

---

## Future Roadmap

### Phase 1: Foundation
- Multi-chain Wallet Manager
- Chain Adapters (Solana & EVM)
- Market Watcher

### Phase 2: Agentic Trading
- Planner Agent (Groq)
- Deterministic Validator
- Executor Service

### Phase 3: Orchestration
- Persistent Workflow State (PostgreSQL)
- Portfolio & Capital Reservation
- Transaction Monitoring

### Phase 4: Advanced Features
- Backtesting Engine
- Strategy Benchmarking
- Multi-strategy support

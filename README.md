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
- SQLite (for workflow persistence)

---

## Architecture

### Modular LangGraph Workflow
The system uses a decoupled LangGraph architecture to separate reasoning from execution:

- **Planner Agent (`src/agents/planner.py`):** Uses Groq (Llama 3) to analyze market data and portfolio state, generating a structured `TradePlan`.
- **Risk Validator (`src/services/risk_validator.py`):** A deterministic node that enforces balance constraints, maximum trade limits, and slippage guardrails.
- **Trade Executor (`src/workflows/nodes.py`):** Dispatches validated actions to chain-specific wallet adapters.

### Prompts & State
- **Prompts:** Managed in `src/prompts/` to ensure clean separation of LLM instructions from logic.
- **State:** Strongly typed `AgentState` defined in `src/workflows/state.py`.

**Note on Market Data:** The `MarketWatcher` service aggregates price snapshots from all configured providers before emitting a single consolidated signal. This ensures that the agent is triggered only once per polling interval with a complete view of the market, effectively preventing redundant agent executions and inefficient resource usage.

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

### Visualization
Generate a visual map of the trading graph:
```bash
make graph
```

### Interactive Debugging
Run the LangGraph dev server to use LangGraph Studio:
```bash
uv run langgraph dev
```

### Run Quality Checks

```bash
# Run comprehensive format check, ruff check, pylint, mypy, pytest, and codespell
make check
```

### Run Tests

```bash
# Run pytest
make test
```

### Integration Testing: Swaps

You can verify the swap logic on each supported chain (Solana Devnet, Ethereum Sepolia, Avalanche Fuji) using the `test_swaps.py` script. This performs a real on-chain transaction (Memo on Solana, Swap on EVM).

```bash
# Solana
uv run scripts/test_swaps.py --chain solana --direction buy --amount 0.001 --asset SOL

# Ethereum Sepolia
uv run scripts/test_swaps.py --chain sepolia --direction buy --amount 1.0 --asset ETH

# Avalanche Fuji
uv run scripts/test_swaps.py --chain avalanche-fuji --direction buy --amount 1.0 --asset AVAX
```

### Configuration

Ensure your `.env` file is configured with the necessary API keys and RPC URLs (especially for reliable Solana Devnet connectivity).

---

## Future Roadmap & Backlog

### Roadmap
- **Phase 1: Foundation** (Completed)
- **Phase 2: Agentic Trading** (Completed - Functional Chain Verified)
- **Phase 3: Real Execution & Persistence** (Next)
- **Phase 4: Advanced Features**

### Backlog
- **Prod-Readiness Assessment:**
  - **Transaction Confirmation:** Currently, the system returns a hash as soon as the transaction is sent. In production, add logic to wait for the transaction to be confirmed/finalized before proceeding with the next step in the workflow.
  - **Retry Logic:** Testnet RPCs are notoriously flaky. Implement exponential backoff retries for all blockchain interactions to prevent transient failures from crashing the agent.
  - **Position Tracking:** Implement a persistence layer (e.g., updating a SQLite DB) to track open positions and realized gains/losses across sessions.
- **Market Data Resilience:** Implement a Binance API fallback in the `MarketWatcher` to ensure service continuity if CoinGecko experiences downtime.
- **RPC Connectivity:** Introduce automatic RPC endpoint fallbacks for chain connectivity to mitigate bottlenecks and ensure reliable transaction submission during high network congestion.
- **Agent Enhancements:** Integrate real-time sentiment analysis, expand asset support, and implement advanced risk management strategies for better decision-making.
- **Backtesting & Simulation:** Develop a backtesting engine to evaluate strategies against historical data before deployment on testnets.

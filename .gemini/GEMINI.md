# GEMINI.md

## Project Context

This repository contains an event-driven, agentic trading simulation platform.

The system trades exclusively on testnets while using real market data to generate signals.
The primary LLM provider is **Groq** for high-speed inference.
**LangSmith** is used for workflow observability and tracing.

Supported chains:

- Solana Devnet (`solana-py`)
- Ethereum Sepolia (`AgentKit/CDP`)
- Avalanche Fuji (`AgentKit/CDP`)

---

# Architectural Constraints

## Plan → Validate → Execute

The system follows a strict separation between planning and execution.

### Agents Generate Plans

Agents produce structured output using Pydantic models to ensure validation and type safety.

Example Plan Model:

```python
from pydantic import BaseModel, Field
from typing import List

class Action(BaseModel):
    action: str = Field(..., description="BUY or SELL")
    asset: str = Field(..., description="Asset symbol e.g. ETH")
    allocation_pct: float = Field(..., ge=0, le=1)

class TradePlan(BaseModel):
    plan_type: str = "trade"
    actions: List[Action]
```

### Executors Execute Plans

Executors perform blockchain operations.

- **EVM Chains:** Use `AgentKit` and the `Coinbase CDP SDK` for swaps and wallet management. `web3.py` may be used for low-level deterministic checks.
- **Solana:** Use `solana-py` for transaction construction and signing.
- Executors must never generate strategy decisions.

---

## Wallet Management & Capital

### Three-Wallet Strategy

The system maintains three distinct wallets, one for each supported chain.

- Each wallet uses **USDC** as its base "bank" currency.
- Trades are simulated by swapping USDC for the target asset and back.

### Programmatic Wallet Creation & Persistence

Wallets should be loaded from environment variables. If not found, they must be created programmatically.

- **EVM:** `AgentKit/CDP` handles wallet persistence. Credentials should be stored in `.env` (API Keys) and wallet data in `*_wallet.json` files.
- **Solana:** The system must generate a keypair if one is not provided in `.env` and store it in a `.solana_wallet` file for future sessions.

### Initialization: Two-Stage Polling

The system operates in two distinct polling stages during startup:

1. **Stage 1: Funding Poll:** The main script polls for native/USDC balances. It will wait indefinitely until at least one wallet is funded. Instructions are provided in `WALLETS.md`.
2. **Stage 2: Market Poll:** Once funds are detected, the system enters its active loop, polling market data providers for signals to trigger the Planner Agent.

### Security

- Agents never see private keys.
- Private keys/CDP credentials must never be logged or committed.
- Wallets are strictly for testnet use.

---

## No Agent-Driven Transaction Construction

Agents propose actions; deterministic services (using AgentKit or solana-py) construct and sign transactions.

---

## Event-Driven Architecture

The system is not request-response driven.
Workflows are resumed through events (MARKET_SIGNAL, TX_CONFIRMED, TX_FAILED, etc.).
Workflows should persist state and sleep while waiting.

---

## Workflow Philosophy

A workflow is not a continuously running agent.
A workflow is a state machine: Start → Generate Plan → Validate → Execute → Wait → Resume → Complete.

---

# Component Responsibilities

## Wallet Manager

Responsibilities:

- Programmatically create/load wallets for all three chains. All wallets must implement the unified interface of `BaseWallet` (`src/services/base_wallet.py`).
- Fetch balances for native tokens and USDC. EVM wallet balances must fetch real USDC balances via contract `read_contract` calls rather than returning 0.0 placeholders.
- Provide wallet addresses for funding.

## Market Watcher

Responsibilities:

- Poll market data providers (e.g., CoinGecko, Binance).
- Detect trading signals and emit events.
  Must not execute trades or modify portfolios.

## Planner Agent

Responsibilities:

- Analyze market state and portfolio state.
- Generate plans using structured output.
  Must not perform execution or sign transactions.

## Validator

Responsibilities:

- Verify balances, wallet availability, position limits, and chain health.
  Must remain deterministic.

## Executor

Responsibilities:

- Execute plans and submit transactions.
- Track transaction identifiers.
  Must not create strategy.

## Transaction Monitor

Responsibilities:

- Poll chain state and verify confirmations/failures.
- Emit workflow events.
  Must not contain LLM logic.

## Portfolio Manager

Responsibilities:

- Track balances, positions, reserved capital, and workflow ownership.
  Must remain deterministic.

---

# Multi-Workflow Execution

Multiple workflows may execute simultaneously (e.g., Workflow A buys ETH, Workflow B buys AVAX). The system must support concurrent execution.

---

# Capital Reservation

Before execution, workflows reserve funds to prevent race conditions. Subsequent workflows must respect these reservations.

---

# Persistence Requirements

Workflow state, pending transactions, plans, portfolio state, and reservations must be recoverable. System restarts must not lose active workflows.

---

# Code Standards

- All public classes, functions, and modules require docstrings.
- Type hints are required.
- Use Pydantic models or dataclasses over generic dictionaries.
- **Standard Logging:** Use Python's standard `logging.getLogger(__name__)` library to trace initialization, RPC activities, and handle failures gracefully. Private keys or API secrets must never be logged.
- **Mandatory Quality Checks:** Before finalizing any task, run `make check` (which comprehensively runs format checks, lints, type checks, unit tests, and spellchecks). All quality checks must pass before reporting the task as complete.

---

# Testing Philosophy

- Every planner decision must be testable independently without blockchain access.
- Executors and monitors must be testable with mocked chain responses.
- Favor deterministic tests.

---

# Preferred Repository Structure

```text
src/
├── agents/
├── workflows/
├── services/
├── chains/
├── models/
├── events/
├── persistence/
├── monitoring/
└── tests/
```

---

# Future Direction

- Portfolio rebalancing, backtesting, strategy benchmarking, multiple planner models, distributed execution, and human approval workflows.

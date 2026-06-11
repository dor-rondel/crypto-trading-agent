# Agentic Testnet Trading System

## Overview

This project is an event-driven, agentic cryptocurrency trading simulation platform built for test networks.

The system executes simulated trading strategies against:

- Solana Devnet
- Ethereum Sepolia
- Avalanche Fuji

Real market data is used to generate trading signals, while all trade execution occurs on testnets to avoid risking real capital.

The architecture is intentionally designed around:

- Plan → Validate → Execute workflows
- Event-driven orchestration
- Persistent workflow state
- Deterministic execution services
- Agentic decision making only where reasoning is required
- **Groq** for high-speed LLM inference
- **LangSmith** for deep observability and tracing

---

## Goals

- Evaluate AI-generated trading strategies safely
- Simulate multi-chain portfolio management
- Test autonomous trading workflows
- Support long-running blockchain operations
- Maintain reproducibility and auditability
- Enable future backtesting and strategy comparison

---

## Core Technologies

### AI / Workflow

- LangGraph
- LangChain
- **Groq** (via LangChain-Groq)
- **LangSmith** (for observability)
- Coinbase AgentKit

### Blockchain

- Solana Python SDK
- web3.py
- Avalanche-compatible EVM tooling

### Infrastructure

- Python 3.12+
- PostgreSQL
- Redis (future)
- Docker (future)

---

## Architecture

### High-Level Flow

Market Watcher

↓

Signal Generated

↓

Planner Agent

↓

Structured Plan

↓

Validator

↓

Executor

↓

Transaction Monitor

↓

Portfolio Manager

---

## Design Principles

### Plan First, Execute Second

Agents do not execute trades directly. They generate structured plans using **Pydantic** models to ensure strict schema validation before execution.

Example Schema:

```python
class TradePlan(BaseModel):
    action: str  # BUY/SELL
    asset: str
    allocation_pct: float
```

Executors are responsible for carrying out plans.

This improves:

- testability
- reproducibility
- observability
- debugging

### Event-Driven Workflows

Workflows are resumed by events.

Examples:

- Transaction confirmed
- Transaction failed
- Bridge completed
- Market signal generated

Workflows should never remain active while waiting.

### Deterministic Services

The following components must remain deterministic:

- Wallet Manager
- Chain Adapters
- Transaction Monitor
- Portfolio Manager
- Capital Reservation Manager

These services must not contain LLM reasoning.

### Wallet Management

Private keys are stored in environment variables (`.env`) and are strictly used by deterministic executors. Agents never have access to wallet secrets.

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
# Run ruff, pylint, and mypy
make lint
```

### Run Tests

```bash
# Run pytest
make test
```

### Run Full Validation

```bash
# Run all checks (format, lint, test, spell)
make check
```

---

## Code Quality Requirements

All code must:

- Pass Ruff
- Pass Pylint
- Pass Mypy
- Pass Pytest
- Pass Codespell

All classes require docstrings.

All public functions require docstrings.

Complex workflows require architecture comments.

---

## Future Roadmap

### Phase 1

- Market watcher
- Planner agent
- Executor
- Solana support
- Sepolia support
- Fuji support

### Phase 2

- Portfolio management
- Capital reservation
- Recovery workflows
- Persistent workflow storage

### Phase 3

- Multi-strategy support
- Backtesting
- Strategy comparison
- Performance analytics

### Phase 4

- CI/CD
- Container deployment
- Distributed workers
- Production observability

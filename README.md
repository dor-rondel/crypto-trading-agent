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

### Deterministic Services
The Wallet Manager, Chain Adapters, and Portfolio Manager must remain deterministic and free of LLM reasoning.

### Three-Wallet USDC Strategy
The system maintains a USDC "bank" on each supported chain. All trades are simulated by swapping USDC for assets and back, ensuring a consistent base currency for performance tracking.

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

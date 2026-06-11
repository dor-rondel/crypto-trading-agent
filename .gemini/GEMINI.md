# GEMINI.md

## Project Context

This repository contains an event-driven, agentic trading simulation platform.

The system trades exclusively on testnets while using real market data to generate signals.
The primary LLM provider is **Groq** for high-speed inference.
**LangSmith** is used for workflow observability and tracing.

Supported chains:
...

- Solana Devnet
- Ethereum Sepolia
- Avalanche Fuji

Future chains may be added.

---

# Architectural Constraints

These constraints are intentional and should not be modified without discussion.

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

Executors must never generate strategy decisions.

---

## Wallet Management

Wallets are managed via environment variables for testnet operations.
Deterministic services (Executors) read private keys from `.env`.

- Agents never see private keys.
- Private keys must never be logged or committed.
- Wallets are strictly for testnet use.

---

## No Agent-Driven Transaction Construction

Agents may propose actions.

Agents may not:

- Construct raw transactions
- Sign transactions
- Directly manage wallets

These responsibilities belong to deterministic services.

---

## Event-Driven Architecture

The system is not request-response driven.

Workflows are resumed through events.

Examples:

- MARKET_SIGNAL
- TX_CONFIRMED
- TX_FAILED
- BRIDGE_COMPLETED

Workflows should persist state and sleep while waiting.

---

## Workflow Philosophy

A workflow is not a continuously running agent.

A workflow is a state machine.

Example:

Start

↓

Generate Plan

↓

Validate

↓

Execute

↓

Wait

↓

Resume

↓

Complete

---

# Component Responsibilities

## Market Watcher

Responsibilities:

- Poll market data providers
- Detect trading signals
- Emit events

Must not execute trades.

Must not modify portfolios.

---

## Planner Agent

Responsibilities:

- Analyze market state
- Analyze portfolio state
- Generate plans

Must not perform execution.

Must not sign transactions.

---

## Validator

Responsibilities:

- Verify balances
- Verify wallet availability
- Verify position limits
- Verify chain health

Must remain deterministic.

---

## Executor

Responsibilities:

- Execute plans
- Submit transactions
- Track transaction identifiers

Must not create strategy.

---

## Transaction Monitor

Responsibilities:

- Poll chain state
- Verify confirmations
- Verify failures
- Emit workflow events

Must not contain LLM logic.

---

## Portfolio Manager

Responsibilities:

- Track balances
- Track positions
- Track reserved capital
- Track workflow ownership

Must remain deterministic.

---

# Multi-Workflow Execution

Multiple workflows may execute simultaneously.

Example:

Workflow A

- Buy ETH

Workflow B

- Buy AVAX

Workflow C

- Bridge SOL

The system must support concurrent execution.

---

# Capital Reservation

Before execution, workflows reserve funds.

Example:

Available USDC: 100

Workflow A reserves: 80

Available balance becomes: 20

Subsequent workflows must respect reservations.

This prevents race conditions.

---

# Persistence Requirements

Workflow state must be recoverable.

Required persistence:

- Workflow state
- Pending transactions
- Plans
- Portfolio state
- Reservations

System restarts must not lose active workflows.

---

# Code Standards

## Mandatory

All public classes require docstrings.

All public functions require docstrings.

All modules require module-level docstrings.

Type hints are required.

Avoid untyped dictionaries where structured models are possible.

Prefer:

- dataclasses
- pydantic models

over generic dictionaries.

---

# Testing Philosophy

Every planner decision should be testable independently.

The planner must be executable without blockchain access.

The executor must be testable with mocked chain adapters.

The transaction monitor must be testable with mocked chain responses.

Favor deterministic tests.

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

Potential future features:

- Portfolio rebalancing
- Backtesting
- Strategy benchmarking
- Multiple planner models
- Distributed workflow execution
- Human approval workflows

Future implementations should preserve the Plan → Validate → Execute architecture.

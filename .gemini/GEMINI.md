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

### Modular Workflows

- **Architecture:** Decouple reasoning from execution using LangGraph. Maintain separate files for nodes, state, and graph definitions.
- **Prompts:** All LLM prompts must reside in `src/prompts/`. Do not hardcode prompts in agent classes.
- **Models:** Use Pydantic models for all inter-node communication (e.g., `TradePlan`, `TradeAction`).
- **Validation:** Every trade plan must pass through a deterministic `RiskValidator` before execution.

### Executors Execute Plans

Executors perform blockchain operations.

- **EVM Chains:** Use `AgentKit` and the `Coinbase CDP SDK` for swaps and wallet management. `web3.py` may be used for low-level deterministic checks.
- **Solana:** Use `solana-py` for transaction construction and signing.
- Executors must never generate strategy decisions.

#### Technical Rationale: Solana Memo Program
On Solana, the system uses the **Memo Program** (`MemoSq9gHqT9VkU4beuy66Gf364aJ6Eic52pD34j3K`) to record trade intents (e.g., `"BUY 1 SOL with 145 USDC"`) directly on-chain.
- **Verifiability:** Every agent decision results in a real transaction hash and a verifiable on-chain record that can be audited via block explorers. This ensures the simulation remains tethered to real-world blockchain activity.
- **Economic Simulation:** It consumes real Devnet SOL for gas, simulating the economic impact and transaction lifecycle of trading without the immediate complexity of full DEX (e.g., Jupiter) integration.
- **Simplicity:** It provides a lightweight way to demonstrate "Proof of Intent" during the prototyping phase while remaining extensible for future DEX integration.


#### Technical Rationale: Wrapped Tokens (WETH/WAVAX)

Native gas tokens (ETH, AVAX) do not follow the ERC-20 standard.

- **Compatibility:** Protocols like Uniswap V3 require ERC-20 compliance.
- **Wrapping:** The system interacts with **WETH** and **WAVAX** contracts to enable seamless swaps with USDC while maintaining exposure to the native asset's price action.

---

## Wallet Management & Capital

### Three-Wallet Strategy

The system maintains three distinct wallets, one for each supported chain.

- Each wallet uses **USDC** as its base "bank" currency.
- Trades are simulated by swapping USDC for the target asset and back.

### Programmatic Wallet Creation & Persistence

Wallets should be loaded from environment variables. If not found, they must be created programmatically.

- **Persistence:** Ensure that mock data (e.g., balance fallbacks) is never persisted to wallet data files.
- **EVM:** `AgentKit/CDP` handles wallet persistence. Credentials should be stored in `.env` (API Keys) and wallet data in `*_wallet.json` files.
- **Solana:** The system must generate a keypair if one is not provided in `.env` and store it in a `.solana_wallet` file for future sessions.

### Initialization: Two-Stage Polling

The system operates in two distinct polling stages during startup:

1. **Stage 1: Funding Poll:** The main script polls for native/USDC balances. It will wait indefinitely until at least one wallet is funded. Instructions are provided in `WALLETS.md`.
2. **Stage 2: Market Poll:** Once funds are detected, the system enters its active loop, polling market data providers for signals to trigger the Planner Agent.

---

## Security

- Agents never see private keys.
- Private keys/CDP credentials must never be logged or committed.
- Wallets are strictly for testnet use.

---

## Event-Driven Architecture

The system is not request-response driven.
Workflows are resumed through events (MARKET_SIGNAL, TX_CONFIRMED, TX_FAILED, etc.).
Workflows should persist state and sleep while waiting.

---

# Component Responsibilities

## Wallet Manager

- Programmatically create/load wallets for all three chains.
- All wallets must implement the unified interface of `BaseWallet`.
- Fetch balances for native tokens and USDC.

## Market Watcher

- Poll market data providers (e.g., CoinGecko, Binance).
- **Batching:** Aggregate price snapshots from all configured providers before emitting a single consolidated signal.

## Planner Agent

- Analyze market state and portfolio state.
- Generate plans using structured output.

## Validator

- Verify balances, wallet availability, position limits, and chain health.
  Must remain deterministic.

## Executor

- Execute plans and submit transactions.
  Must remain deterministic.

---

# Persistence Requirements

Workflow state, pending transactions, plans, portfolio state, and reservations must be recoverable. SQLite is used for local workflow persistence via LangGraph checkpointers.

---

# Code Standards

- All public classes, functions, and modules require docstrings.
- Type hints are required.
- Use Pydantic models or dataclasses over generic dictionaries.
- **Standard Logging:** Use Python's standard `logging.getLogger(__name__)`.
- **Mandatory Quality Checks:** Before finalizing any task, run `make check`.
on's standard `logging.getLogger(__name__)`.
- **Mandatory Quality Checks:** Before finalizing any task, run `make check`.

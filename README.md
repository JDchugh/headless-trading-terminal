# Python Algorithmic Trading Engine

An event-driven algorithmic trading engine built in Python.

This project implements a decoupled, asynchronous architecture to manage live market data streams, signal generation, and order execution. It includes a paper-trading simulator and a state-reconciliation system designed to handle unexpected disconnects or crashes.

## Core Architecture

The engine is built around `asyncio` to handle concurrent I/O operations without blocking the main thread.

* **Asynchronous Workers:** The orchestrator (`main.py`) manages several concurrent queues:
  * **Tick Streamer:** Consumes raw tick data from the broker websocket.
  * **Timer Worker:** Enforces strict minute-boundaries for accurate OHLCV candle aggregation.
  * **Strategy Engine:** Evaluates incoming candles against active strategies.
  * **Execution Worker:** Handles asynchronous dispatch of market and limit orders.
* **Pub/Sub Routing:** To efficiently handle multiple instruments, the engine builds a dynamic routing map (`strategy_symbol_map`). Incoming candles are routed in `O(1)` time only to the specific strategies subscribed to that symbol.
* **Abstract Broker Interface:** Trading logic is decoupled from broker APIs via a `BaseBroker` interface (Dependency Injection). The system currently supports local simulation (`FakeBroker`) through a `UnifiedBroker` facade.

## State Management & Recovery

* **Position Reconciler:** On boot, the engine downloads the true order book from the broker, calculates the net position per strategy, and synchronizes the local state to match the broker's source of truth.
* **In-Memory Cache:** `StateManager` uses an in-memory cache to serialize strategy state (EMAs, boundaries) to disk, preventing read-modify-write race conditions when multiple strategies trigger simultaneously.

## Project Structure

```
├── main.py                # Async Orchestrator & Worker Definitions
├── data_manager.py        # Multi-asset real-time candle aggregation
├── strategy.py            # Signal generation logic (EMA Crossover)
├── utils.py               # Candle boundary detection & multi-timeframe resampling
├── reconciler.py          # Boot-sequence position verification
├── state_manager.py       # Thread-safe disk serialization for state
└── brokers/
    ├── base_broker.py     # Abstract Interface
    ├── unified_broker.py  # Broker Facade / Router
    ├── fake_broker.py     # Offline Paper Trading Simulator
    └── kotak_broker.py    # Kotak Neo API Implementation
```

## Current Roadmap

* **Base Strategy Interface:** Refactoring signal generation to enforce strict position guards and risk management at the interface level.
* **P&L Tracking:** Implementing real-time realized and unrealized P&L calculation modules.
* **Warmup Sequence:** Pre-fetching historical candles on boot to seed technical indicators before live streaming begins.
* **Error & Failure Handling:** System is currently an MVP focused strictly on the happy path. Comprehensive error handling (network disconnects, order rejections, rate limits) is slated for the next development phase.
* **Live Broker Integrations:** `KotakBroker` and `ICICIBroker` currently have their architectural interfaces wired up but require complete implementation before live deployment.
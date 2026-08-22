import asyncio
import time
from datetime import datetime
from brokers import UnifiedBroker
from data_manager import DataManager
from strategy import Strategy
from state_manager import StateManager
from reconciler import PositionReconciler
from logger_setup import setup_logger

logger = setup_logger()

# ---------------------------------------------------------
# Worker 1: The Tick Streamer
# Connects the Broker's generic tick stream to the DataManager
# ---------------------------------------------------------
async def tick_stream_worker(broker, data_manager, instruments: list[tuple[str, str]], tick_counter: dict):
    try:
        async for tick in broker.stream_ticks(instruments):
            data_manager.process_ltp(tick["symbol"], tick["ltp"])
            tick_counter["count"] += 1
    except asyncio.CancelledError:
        logger.warning("Tick stream worker cancelled.")

# ---------------------------------------------------------
# Worker: Heartbeat Timer
# ---------------------------------------------------------
async def heartbeat_worker(tick_counter: dict):
    try:
        while True:
            await asyncio.sleep(10)
            logger.info(f"[Heartbeat] Processed {tick_counter['count']} ticks in the last 10 seconds.")
            tick_counter["count"] = 0
    except asyncio.CancelledError:
        logger.warning("Heartbeat worker cancelled.")

# ---------------------------------------------------------
# Worker 2: The Timer
# Wakes up every minute, forces a candle close, throws it on the queue
# ---------------------------------------------------------
async def timer_worker(data_manager, candle_queue, shutdown_event):
    logger.info("Timer worker started. Waiting for minute boundaries...")
    try:
        while True:
            current_time = time.time()
            seconds_to_next_minute = 60 - (current_time % 60)
            await asyncio.sleep(seconds_to_next_minute)

            now = datetime.now()
            if now.hour == 15 and now.minute >= 30:
                logger.info("Market is closed. Pulling the shutdown alarm!")
                shutdown_event.set()
                break
                
            boundary_timestamp = int(current_time - (current_time % 60))
            candles = data_manager.close_candles(boundary_timestamp)

            for candle in candles:
                await candle_queue.put(candle)
    except asyncio.CancelledError:
        logger.warning("Timer worker cancelled.")

# ---------------------------------------------------------
# The Single Engine Strategy Worker
# ---------------------------------------------------------
async def strategy_engine_worker(strategy_symbol_map, candle_queue, signal_queue):
    try:
        while True:
            candle = await candle_queue.get()
            symbol = candle.get("symbol")
            
            # Instantly grab ONLY the strategies that care about this symbol
            for strategy in strategy_symbol_map.get(symbol, []):
                try:
                    signal = strategy.process_candle(candle)
                    if signal:
                        await signal_queue.put(signal)
                except Exception as e:
                    logger.error(f"Strategy {strategy.name} crashed: {e}")
                    
            candle_queue.task_done()
    except asyncio.CancelledError:
        logger.warning("Strategy Engine cancelled.")

# ---------------------------------------------------------
# Worker 3: The Execution Broker
# Pulls signals from the queue, executes real trades
# ---------------------------------------------------------
async def execution_worker(broker, signal_queue):
    try:
        while True:
            signal = await signal_queue.get()
            broker.place_order(**signal)
            signal_queue.task_done()
    except asyncio.CancelledError:
        logger.warning("Execution worker cancelled.")

# ---------------------------------------------------------
# The Orchestrator (Main)
# Starts the workers, connects the queues, waits for shutdown alarm
# ---------------------------------------------------------
async def main():
    broker = UnifiedBroker()
    broker.connect()
    data_manager = DataManager()
    state_manager = StateManager()
    
    # We can now effortlessly add multiple strategies on different timeframes!
    strategies = [
        Strategy(state_manager, name="EMA_5m", symbol="Nifty 50", exchange="nse_cm", short_period=9, long_period=20, target_timeframe=5),
        Strategy(state_manager, name="EMA_1m", symbol="Nifty 50", exchange="nse_cm", short_period=5, long_period=10, target_timeframe=1)
    ]
    
    # --- BUILD THE ROUTING MAP ---
    strategy_symbol_map = {}
    for strat in strategies:
        strategy_symbol_map.setdefault(strat.symbol, []).append(strat)
    # -----------------------------

    # --- RECONCILIATION BOOT SEQUENCE ---
    reconciler = PositionReconciler()
    reconciler.synchronize(broker, strategies)
    # ------------------------------------

    candle_queue = asyncio.Queue()
    signal_queue = asyncio.Queue()
    shutdown_event = asyncio.Event()
    tick_counter = {"count": 0}
    # Automatically figure out what instruments the broker needs to subscribe to
    unique_instruments = list({(strat.exchange, strat.symbol) for strat in strategies})

    tasks = [
        asyncio.create_task(tick_stream_worker(broker, data_manager, unique_instruments, tick_counter)),
        asyncio.create_task(heartbeat_worker(tick_counter)),
        asyncio.create_task(timer_worker(data_manager, candle_queue, shutdown_event)),
        asyncio.create_task(strategy_engine_worker(strategy_symbol_map, candle_queue, signal_queue)),
        asyncio.create_task(execution_worker(broker, signal_queue))
    ]

    logger.info("All queues and workers running. System is online.")
    await shutdown_event.wait()
    
    logger.info("Shutdown signal received. Executing Graceful Closure...")
    for task in tasks:
        task.cancel()
        
    await broker.close_stream()
    await asyncio.gather(*tasks, return_exceptions=True)
    logger.info("Application safely terminated.")

if __name__ == "__main__":
    asyncio.run(main())

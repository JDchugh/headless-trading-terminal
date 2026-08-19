import asyncio
import time
from datetime import datetime
from broker import KotakBroker
from data_manager import DataManager
from strategy import Strategy

# ---------------------------------------------------------
# Worker 1: The Tick Streamer
# Connects the Broker's generic tick stream to the DataManager
# ---------------------------------------------------------
async def tick_stream_worker(broker, data_manager, exchange, instrument):
    try:
        async for ltp in broker.stream_ticks(exchange, instrument):
            data_manager.process_ltp(ltp)
    except asyncio.CancelledError:
        print("Tick stream worker cancelled.")

# ---------------------------------------------------------
# Worker 2: The Timer
# Wakes up every minute, forces a candle close, throws it on the queue
# ---------------------------------------------------------
async def timer_worker(data_manager, candle_queue, shutdown_event):
    print("Timer worker started. Waiting for minute boundaries...")
    try:
        while True:
            current_time = time.time()
            seconds_to_next_minute = 60 - (current_time % 60)
            await asyncio.sleep(seconds_to_next_minute)

            now = datetime.now()
            if now.hour == 15 and now.minute >= 30:
                print("Market is closed. Pulling the shutdown alarm!")
                shutdown_event.set()
                break
                
            boundary_timestamp = int(current_time - (current_time % 60))
            candle = data_manager.close_candle(boundary_timestamp)

            if candle is not None:
                await candle_queue.put(candle)
    except asyncio.CancelledError:
        print("Timer worker cancelled.")

# ---------------------------------------------------------
# The Single Engine Strategy Worker
# ---------------------------------------------------------
async def strategy_engine_worker(all_strategies, candle_queue, signal_queue):
    try:
        while True:
            candle = await candle_queue.get()
            
            # The Engine evaluates all strategies sequentially
            for strategy in all_strategies:
                try:
                    signal = strategy.process_candle(candle)
                    if signal:
                        await signal_queue.put(signal)
                except Exception as e:
                    print(f"[ERROR] Strategy {strategy.short_period}/{strategy.long_period} crashed: {e}")
                    
            candle_queue.task_done()
    except asyncio.CancelledError:
        print("Strategy Engine cancelled.")

# ---------------------------------------------------------
# Worker 3: The Execution Broker
# Pulls signals from the queue, executes real trades
# ---------------------------------------------------------
async def execution_worker(broker, signal_queue):
    try:
        while True:
            signal = await signal_queue.get()
            broker.place_order(side=signal["side"], quantity=signal["quantity"])
            signal_queue.task_done()
    except asyncio.CancelledError:
        print("Execution worker cancelled.")

# ---------------------------------------------------------
# The Orchestrator (Main)
# Starts the workers, connects the queues, waits for shutdown alarm
# ---------------------------------------------------------
async def main():
    broker = KotakBroker()
    broker.connect()
    data_manager = DataManager()
    
    # We can now effortlessly add multiple strategies on different timeframes!
    strategies = [
        Strategy(short_period=9, long_period=20, target_timeframe=5),
        Strategy(short_period=5, long_period=10, target_timeframe=1)
    ]

    candle_queue = asyncio.Queue()
    signal_queue = asyncio.Queue()
    shutdown_event = asyncio.Event()

    tasks = [
        asyncio.create_task(tick_stream_worker(broker, data_manager, "nse_cm", "Nifty 50")),
        asyncio.create_task(timer_worker(data_manager, candle_queue, shutdown_event)),
        asyncio.create_task(strategy_engine_worker(strategies, candle_queue, signal_queue)),
        asyncio.create_task(execution_worker(broker, signal_queue))
    ]

    print("\n[ORCHESTRATOR] All queues and workers running. System is online.")
    await shutdown_event.wait()
    
    print("\n[ORCHESTRATOR] Shutdown signal received. Executing Graceful Closure...")
    for task in tasks:
        task.cancel()
        
    await broker.close_stream()
    await asyncio.gather(*tasks, return_exceptions=True)
    print("[ORCHESTRATOR] Application safely terminated.")

if __name__ == "__main__":
    asyncio.run(main())

import asyncio
import random
import json
import os
import time
from typing import AsyncGenerator
from datetime import datetime

from .base_broker import BaseBroker
from logger_setup import setup_logger

logger = setup_logger()

class FakeBroker(BaseBroker):
    def __init__(self, db_path="fake_broker_db.json"):
        self.db_path = db_path
        self.latest_prices = {}  # Tracks the live LTP for accurate market order fills!
        self._ensure_db_exists()
        
    def _ensure_db_exists(self):
        """Creates the fake database if it doesn't exist."""
        if not os.path.exists(self.db_path):
            with open(self.db_path, "w") as f:
                json.dump({"orders": []}, f)
                
    def _read_db(self):
        with open(self.db_path, "r") as f:
            return json.load(f)
            
    def _write_db(self, data):
        with open(self.db_path, "w") as f:
            json.dump(data, f, indent=4)

    def connect(self) -> bool:
        logger.info("FakeBroker connected to Local Simulator.")
        return True

    async def stream_ticks(self, instruments: list[tuple[str, str]]) -> AsyncGenerator[dict, None]:
        """Simulates a live market feed using a random walk."""
        logger.info(f"FakeBroker started streaming for {instruments}")
        
        # Starting price
        current_price = 24000.0 
        
        while True:
            # Generate a random price movement between -2 and +2
            current_price += random.uniform(-2, 2)
            
            for exchange, symbol in instruments:
                ltp = round(current_price, 2)
                self.latest_prices[symbol] = ltp  # Save LTP for Market Orders!
                
                yield {
                    "symbol": symbol,
                    "ltp": ltp,
                    "timestamp": time.time()
                }
            await asyncio.sleep(1) # Fake tick every 1 second

    async def close_stream(self):
        logger.info("FakeBroker stream closed safely.")

    def fetch_historical_candles(self, symbol: str, exchange: str, start_time: datetime, end_time: datetime, timeframe: str) -> list[dict]:
        logger.warning("FakeBroker does not support historical candles yet.")
        return []

    def place_order(self, strategy: str, symbol: str, exchange: str, side: str, quantity: int, order_type: str = "MARKET", product_type: str = "MIS", price: float = 0.0, trigger_price: float = 0.0) -> str:
        """Executes the order and saves it to the persistent JSON DB."""
        db = self._read_db()
        
        order_id = f"fake_{int(time.time())}"
        
        # If MARKET order (price=0), fetch the actual simulated LTP!
        # If LTP isn't tracked yet, default to 24000.0
        execution_price = price if price > 0 else self.latest_prices.get(symbol, 24000.0)
        
        new_order = {
            "id": order_id, 
            "tag": strategy,
            "symbol": symbol, 
            "side": side, 
            "quantity": quantity,
            "price": execution_price,
            "status": "COMPLETE",
            "timestamp": time.time()
        }
        
        db["orders"].append(new_order)
        self._write_db(db)
        
        logger.info(f"[FakeBroker] Executed {side} {quantity} {symbol} @ {execution_price} (Tag: {strategy})")
        return order_id
        
    def modify_order(self, order_id: str, quantity: int = None, price: float = None) -> bool:
        logger.warning("FakeBroker modify_order not implemented.")
        return False

    def cancel_order(self, order_id: str) -> bool:
        logger.warning("FakeBroker cancel_order not implemented.")
        return False

    def get_order_status(self, order_id: str) -> dict:
        db = self._read_db()
        for o in db["orders"]:
            if o["id"] == order_id:
                return {"status": o["status"]}
        return {"status": "UNKNOWN"}

    def get_order_book(self) -> list[dict]:
        db = self._read_db()
        return db["orders"]



    def get_positions(self) -> list[dict]:
        db = self._read_db()
        positions_map = {}
        
        for o in db["orders"]:
            if o["status"] == "COMPLETE":
                sym = o["symbol"]
                qty = o["quantity"] if o["side"] == "BUY" else -o["quantity"]
                positions_map[sym] = positions_map.get(sym, 0) + qty
                
        return [
            {
                "symbol": sym,
                "net_quantity": qty,
                "product_type": "MIS"
            }
            for sym, qty in positions_map.items() if qty != 0
        ]

from typing import AsyncGenerator
from datetime import datetime

from .base_broker import BaseBroker
from .fake_broker import FakeBroker

class UnifiedBroker(BaseBroker):
    def __init__(self):
        # TEMPORARY: Using FakeBroker for testing
        self.data_broker = FakeBroker()
        self.execution_broker = self.data_broker
        
    def connect(self) -> bool:
        # Connect both APIs!
        self.data_broker.connect()
        if self.data_broker is not self.execution_broker:
            self.execution_broker.connect()
        return True

    async def stream_ticks(self, instruments: list[tuple[str, str]]) -> AsyncGenerator[dict, None]:
        # Route to Data Provider
        async for tick in self.data_broker.stream_ticks(instruments):
            yield tick

    async def close_stream(self):
        await self.data_broker.close_stream()
            
    def fetch_historical_candles(self, symbol: str, exchange: str, start_time: datetime, end_time: datetime, timeframe: str) -> list[dict]:
        return self.data_broker.fetch_historical_candles(symbol, exchange, start_time, end_time, timeframe)

    def place_order(self, strategy: str, symbol: str, exchange: str, side: str, quantity: int, order_type: str = "MARKET", product_type: str = "MIS", price: float = 0.0, trigger_price: float = 0.0) -> str:
        # Route to Execution Provider
        return self.execution_broker.place_order(strategy, symbol, exchange, side, quantity, order_type, product_type, price, trigger_price)
        
    def modify_order(self, order_id: str, quantity: int = None, price: float = None) -> bool:
        return self.execution_broker.modify_order(order_id, quantity, price)

    def cancel_order(self, order_id: str) -> bool:
        return self.execution_broker.cancel_order(order_id)
        
    def get_positions(self) -> list[dict]:
        return self.execution_broker.get_positions()
        
    def get_order_status(self, order_id: str) -> dict:
        return self.execution_broker.get_order_status(order_id)

    def get_order_book(self) -> list[dict]:
        return self.execution_broker.get_order_book()

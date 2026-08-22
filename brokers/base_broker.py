from abc import ABC, abstractmethod
from typing import AsyncGenerator
from datetime import datetime

class BaseBroker(ABC):
    # --- Lifecycle & Data ---
    @abstractmethod
    def connect(self) -> bool:
        """Authenticates the broker API."""
        pass

    @abstractmethod
    async def stream_ticks(self, instruments: list[tuple[str, str]]) -> AsyncGenerator[dict, None]:
        """Yields: {'symbol': 'RELIANCE', 'timestamp': 1724, 'ltp': 2500.5}"""
        pass

    @abstractmethod
    async def close_stream(self):
        """Closes the active tick stream connection."""
        pass
    
    @abstractmethod
    def fetch_historical_candles(self, symbol: str, exchange: str, start_time: datetime, end_time: datetime, timeframe: str) -> list[dict]:
        """Returns standard OHLCV list for the Warmup sequence."""
        pass

    # --- Execution ---
    @abstractmethod
    def place_order(self, strategy: str, symbol: str, exchange: str, side: str, quantity: int, order_type: str = "MARKET", product_type: str = "MIS", price: float = 0.0, trigger_price: float = 0.0) -> str:
        """Executes an order and returns a unique Order ID."""
        pass
    
    @abstractmethod
    def modify_order(self, order_id: str, quantity: int = None, price: float = None) -> bool:
        """Updates a pending limit/stop order."""
        pass

    @abstractmethod
    def cancel_order(self, order_id: str) -> bool:
        """Cancels a specific pending order."""
        pass


    # --- Reconciliation ---
    @abstractmethod
    def get_positions(self) -> list[dict]:
        """Returns normalized list of current intraday holdings."""
        pass

    @abstractmethod
    def get_order_status(self, order_id: str) -> dict:
        """Returns the status of an order (COMPLETE, REJECTED, PENDING, HALF-FILLED, CANCELLED)."""
        pass
        
    @abstractmethod
    def get_order_book(self) -> list[dict]:
        """Returns all completed orders for the day, including their tags."""
        pass

import json
import os
import asyncio
from typing import AsyncGenerator
from datetime import datetime
from dotenv import load_dotenv
from neo_api_client import NeoAPI
from neo_api_client.websocket.feed import WsToken

from .base_broker import BaseBroker
from .kotak_scrip_master import KotakScripMaster
from logger_setup import setup_logger

logger = setup_logger()

class KotakBroker(BaseBroker):
    def __init__(self):
        self.client = None
        self.ws = None
        self.scrip_master = KotakScripMaster()

    def connect(self) -> bool:
        # Build the Scrip Master FIRST!
        self.scrip_master.build_master()
        
        load_dotenv()
        with open("token.json", "r") as file:
            session_data = json.load(file)

        self.client = NeoAPI(
            environment="prod",
            consumer_key=os.getenv("KOTAK_CONSUMER_KEY")
        )

        config = self.client.configuration
        config.edit_token = session_data["token"]
        config.edit_sid = session_data["sid"]
        config.edit_rid = session_data["rid"]
        config.base_url = session_data["baseUrl"]
        config.data_center = session_data["dataCenter"]
        config.ucc = session_data["ucc"]
        config.resolve_dynamic_urls(self.client.api_client.rest_client)

        logger.info("KotakBroker connected using saved session.")
        return True

    async def stream_ticks(self, instruments: list[tuple[str, str]]) -> AsyncGenerator[dict, None]:
        tokens = []
        for exchange, symbol in instruments:
            token = self.scrip_master.get_token(exchange, symbol)
            if token:
                tokens.append(WsToken(exchange, token))
                
        if not tokens:
            logger.warning("No valid tokens found to stream.")
            return

        self.ws = self.client.create_websocket()
        async with self.ws:
            await self.ws.subscribe_index(tokens)
            logger.info(f"Subscribed to {len(tokens)} instruments. Streaming ticks...")
            
            async for message in self.ws:
                # Inbound translation
                symbol = self.scrip_master.get_symbol(message.instrument_token)
                if symbol:
                    yield {
                        "symbol": symbol,
                        "ltp": float(message.last_traded_price),
                        "timestamp": message.exchange_timestamp
                    }

    async def close_stream(self):
        if self.ws:
            await self.ws.close()
            
    def fetch_historical_candles(self, symbol: str, exchange: str, start_time: datetime, end_time: datetime, timeframe: str) -> list[dict]:
        raise NotImplementedError("Kotak Neo API does not support historical data. Use ICICIBroker instead.")

    def place_order(self, strategy: str, symbol: str, exchange: str, side: str, quantity: int, order_type: str = "MARKET", product_type: str = "MIS", price: float = 0.0, trigger_price: float = 0.0) -> str:
        token = self.scrip_master.get_token(exchange, symbol)
        if not token:
            logger.error(f"Cannot place order for unknown symbol {symbol}")
            return "UNKNOWN_TOKEN"

        logger.info(f"SIGNAL EXECUTED for Strategy: {strategy} -> {side} {quantity} {symbol} (Token: {token})")
        # Real API call goes here:
        # res = self.client.place_order(
        #     instrument_token=token, exchange_segment=exchange, transaction_type=side,
        #     quantity=str(quantity), order_type=order_type, product=product_type,
        #     price=str(price), trigger_price=str(trigger_price),
        #     amo="NO", validity="DAY", dtc="1", tag=strategy
        # )
        # return res.get("nOrdNo", "DUMMY_ID")
        
        return "DUMMY_ID_FOR_NOW"
        
    def modify_order(self, order_id: str, quantity: int = None, price: float = None) -> bool:
        logger.warning(f"Modify order {order_id} not implemented yet.")
        return False

    def cancel_order(self, order_id: str) -> bool:
        logger.warning(f"Cancel order {order_id} not implemented yet.")
        return False
        
    def get_positions(self) -> list[dict]:
        return []

    def get_order_status(self, order_id: str) -> dict:
        return {"order_id": order_id, "status": "UNKNOWN"}

    def get_order_book(self) -> list[dict]:
        # res = self.client.order_report()
        # return [normalize(o) for o in res]
        logger.warning("KotakBroker get_order_book not implemented. Returning empty list.")
        return []

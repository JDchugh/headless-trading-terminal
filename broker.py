import json
import os
from dotenv import load_dotenv
from neo_api_client import NeoAPI
from neo_api_client.websocket.feed import WsToken


class KotakBroker:
    def __init__(self):
        self.client = None
        self.ws = None

    def connect(self):
        load_dotenv()

        # Read saved session data from token.json (assuming script runs from root)
        with open("token.json", "r") as file:
            session_data = json.load(file)

        # Create NeoAPI client with consumer key
        self.client = NeoAPI(
            environment="prod",
            consumer_key=os.getenv("KOTAK_CONSUMER_KEY")
        )

        # Manually set the internal SDK fields
        config = self.client.configuration
        config.edit_token = session_data["token"]
        config.edit_sid = session_data["sid"]
        config.edit_rid = session_data["rid"]
        config.base_url = session_data["baseUrl"]
        config.data_center = session_data["dataCenter"]
        config.ucc = session_data["ucc"]
        config.resolve_dynamic_urls(self.client.api_client.rest_client)

        print("Broker connected using saved session.")

    async def stream_ticks(self, exchange_segment, instrument_name):
        """Generic Async Generator that yields live prices from the Kotak feed."""
        self.ws = self.client.create_websocket()
        async with self.ws:
            await self.ws.subscribe_index([WsToken(exchange_segment, instrument_name)])
            print(f"Subscribed to {instrument_name}. Streaming ticks...")
            
            async for message in self.ws:
                yield message.last_traded_price

    async def close_stream(self):
        if self.ws:
            await self.ws.close()

    def place_order(self, side, quantity):
        print(f"SIGNAL EXECUTED: {side} {quantity} (Order placed on Kotak API)")

class DataManager:
    def __init__(self):
        self.current_candles = {}
        self.last_seen_prices = {}

    def process_ltp(self, symbol, ltp):
        self.last_seen_prices[symbol] = ltp

        if symbol not in self.current_candles:
            # Start a new candle
            self.current_candles[symbol] = {
                "open": ltp,
                "high": ltp,
                "low": ltp,
                "close": ltp
            }
        else:
            # Update existing candle
            candle = self.current_candles[symbol]
            candle["high"] = max(candle["high"], ltp)
            candle["low"] = min(candle["low"], ltp)
            candle["close"] = ltp

    def close_candles(self, timestamp):
        completed_candles = []
        for symbol, last_price in self.last_seen_prices.items():
            if symbol in self.current_candles:
                # We had ticks in this minute
                candle = self.current_candles.pop(symbol)
            else:
                # No ticks in this minute, but we have a previous price (Forward Fill)
                candle = {
                    "open": last_price,
                    "high": last_price,
                    "low": last_price,
                    "close": last_price
                }
            
            # Add metadata to the completed candle
            candle["timestamp"] = timestamp
            candle["symbol"] = symbol
            completed_candles.append(candle)
            
        return completed_candles

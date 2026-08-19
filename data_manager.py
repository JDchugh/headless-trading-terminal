class DataManager:
    def __init__(self):
        self.current_candle = None
        self.last_seen_price = None

    def process_ltp(self, ltp):
        self.last_seen_price = ltp

        if self.current_candle is None:
            # Start a new candle
            self.current_candle = {
                "open": ltp,
                "high": ltp,
                "low": ltp,
                "close": ltp
            }
        else:
            # Update existing candle
            self.current_candle["high"] = max(self.current_candle["high"], ltp)
            self.current_candle["low"] = min(self.current_candle["low"], ltp)
            self.current_candle["close"] = ltp

    def close_candle(self, timestamp):
        if self.current_candle is not None:
            # We had ticks in this minute
            completed_candle = self.current_candle
        elif self.last_seen_price is not None:
            # No ticks in this minute, but we have a previous price (Forward Fill)
            completed_candle = {
                "open": self.last_seen_price,
                "high": self.last_seen_price,
                "low": self.last_seen_price,
                "close": self.last_seen_price
            }
        else:
            # Edge case: No ticks ever received yet (app just started)
            return None

        # Add the timestamp to the completed candle
        completed_candle["timestamp"] = timestamp

        # Reset current candle for the next minute
        self.current_candle = None
        return completed_candle

from utils import resample_to_timeframe, is_candle_boundary

class Strategy:
    def __init__(self, short_period=9, long_period=20, target_timeframe=1):
        self.short_period = short_period
        self.long_period = long_period
        self.target_timeframe = target_timeframe
        
        self.candle_buffer = []  # Our transparent buffer!
        
        self.short_ema = None
        self.long_ema = None
        self.previous_short_ema = None
        self.previous_long_ema = None

    def process_candle(self, candle):
        # 1. Add the raw 1-minute candle to the buffer
        self.candle_buffer.append(candle)
        
        # 2. Check the mathematical boundary
        if not is_candle_boundary(candle["timestamp"], self.target_timeframe):
            return None
            
        # 3. Boundary hit! Convert the buffer into a higher timeframe candle
        htf_candle = resample_to_timeframe(self.candle_buffer)
        self.candle_buffer.clear()
        
        # 4. Now run the standard EMA math on the aggregated candle
        price = htf_candle["close"]
        
        self.previous_short_ema = self.short_ema
        self.previous_long_ema = self.long_ema

        self.short_ema = self.calculate_ema(price, self.short_ema, self.short_period)
        self.long_ema = self.calculate_ema(price, self.long_ema, self.long_period)

        print(f"[{self.target_timeframe}m Candle] Price: {price} | EMA{self.short_period}: {self.short_ema:.2f} | EMA{self.long_period}: {self.long_ema:.2f}")

        return self.check_crossover()

    def calculate_ema(self, price, previous_ema, period):
        if previous_ema is None:
            return price

        alpha = 2 / (period + 1)

        return (
            alpha * price
            + (1 - alpha) * previous_ema
        )

    def check_crossover(self):
        if (
            self.previous_short_ema is None
            or self.previous_long_ema is None
        ):
            return None

        crossed_up = (
            self.previous_short_ema <= self.previous_long_ema
            and
            self.short_ema > self.long_ema
        )

        crossed_down = (
            self.previous_short_ema >= self.previous_long_ema
            and
            self.short_ema < self.long_ema
        )

        if crossed_up:
            return {"side": "BUY", "quantity": 1}

        if crossed_down:
            return {"side": "SELL", "quantity": 1}

        return None

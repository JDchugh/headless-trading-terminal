from utils import resample_to_timeframe, is_candle_boundary
from logger_setup import setup_logger

logger = setup_logger()

class Strategy:
    def __init__(self, state_manager, name="EMA_Strategy", symbol="Nifty 50", exchange="nse_cm", short_period=9, long_period=20, target_timeframe=1):
        self.state_manager = state_manager
        self.name = name
        self.symbol = symbol
        self.exchange = exchange
        self.short_period = short_period
        self.long_period = long_period
        self.target_timeframe = target_timeframe
        
        self.candle_buffer = []  # Our transparent buffer!
        
        self.short_ema = None
        self.long_ema = None
        self.previous_short_ema = None
        self.previous_long_ema = None
        
        self.current_position = 0
        
        # Restore State on Boot
        saved_state = self.state_manager.load_state(self.name)
        if saved_state:
            self.short_ema = saved_state.get("short_ema")
            self.long_ema = saved_state.get("long_ema")
            self.current_position = saved_state.get("current_position", 0)
            logger.info(f"[{self.name}] Math Restored: Pos={self.current_position}, short_ema={self.short_ema}, long_ema={self.long_ema}")

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

        logger.debug(f"[{self.target_timeframe}m Candle] Price: {price} | EMA{self.short_period}: {self.short_ema:.2f} | EMA{self.long_period}: {self.long_ema:.2f}")

        # Checkpoint the Math!
        self.state_manager.save_state(self.name, {
            "short_ema": self.short_ema,
            "long_ema": self.long_ema,
            "current_position": self.current_position,
            "last_timestamp": candle["timestamp"]
        })

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

        base_signal = {
            "strategy": self.name,
            "symbol": self.symbol,
            "exchange": self.exchange,
            "quantity": 1
        }

        if crossed_up:
            return {**base_signal, "side": "BUY"}

        if crossed_down:
            return {**base_signal, "side": "SELL"}

        return None

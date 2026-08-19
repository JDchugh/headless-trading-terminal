def resample_to_timeframe(candle_list):
    """Takes a list of 1-minute candles and aggregates them into a single Higher Timeframe OHLC candle."""
    if not candle_list:
        return None
        
    return {
        "timestamp": candle_list[0]["timestamp"],
        "open": candle_list[0]["open"],
        "high": max(c["high"] for c in candle_list),
        "low": min(c["low"] for c in candle_list),
        "close": candle_list[-1]["close"]
    }

def is_candle_boundary(timestamp, target_timeframe):
    """Checks if the UTC timestamp completes the timeframe boundary for the NSE market (09:15 open)."""
    ts_ist = timestamp + 19800
    seconds_since_midnight = ts_ist % 86400
    minutes_since_open = int((seconds_since_midnight - 33300) / 60)
    
    return (minutes_since_open + 1) % target_timeframe == 0

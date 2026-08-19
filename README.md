DataMAnager -> 
object = owns a candle, last_seens_price as properties and process_ltp and close_candle as functions
process_ltp(ltp) = takes ltp(from broker) and updates candle
close_candle(timestamp) = takes timestamp and close the candle for the same timestemp and return it

Strategy ->
object = owns short_ema and long_ema as properties and accept same as parameters. Has process_candle as function.
process_candle(candle) = takes candle and return buy/sell signal if there is any

broker ->
object = has client and ws as properties. connect, async stream_ticks, async close_stream, and place_order as functions/generators.
connect() = connects the broker
stream_ticks("nse_cm", "Nifty 50") = takes exchange and instrument and yields ltp of the instrument
close_stream = closes the ws connection
place_order(side, quantity) = takes side and quantity and places order on broker(right now just print only, not made it functional yet)


utils ->
is_candle_boundary(timestamp, time_frame) = takes timestamp and time_frame and return true if candle is boundary for that same timeframe. timeframe is in minutes

resample_to_timeframe(candle_list) = takes list of candles and return aggregated candle in form of dict(same format as candle)
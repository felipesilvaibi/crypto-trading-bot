import time

import pandas as pd
import pandas_ta as ta
import schedule
from ta.momentum import RSIIndicator

from src.binance_futures_trading_helper import BinanceFuturesTradingHelper


class WeaponCandleStrategy:
    def job(self):
        # conexão
        helper = BinanceFuturesTradingHelper()

        # definir par
        symbol = "BTCUSDT"

        # rodar PNL
        helper.binance.cancel_all_orders(symbol=symbol)
        loss = -4
        target = 8
        helper.close_pnl_position(symbol=symbol, loss=loss, target=target)

        # tamanho maximo, tamanho da ordem, loss, gain
        posicao_max = 0.004
        posicao = 0.002

        # importar candles
        timeframe = "30m"
        bars = helper.binance.fetch_ohlcv(symbol, timeframe, limit=48)
        df_candles = pd.DataFrame(
            bars, columns=["time", "abertura", "max", "min", "fechamento", "volume"]
        )
        df_candles["time"] = pd.to_datetime(
            df_candles["time"], unit="ms", utc=True
        ).map(lambda x: x.tz_convert("America/Sao_Paulo"))

        # criar métricas da estratégia
        rsi = RSIIndicator(df_candles["fechamento"], window=14)
        df_candles["rsi"] = rsi.rsi()

        ema_20 = ta.ema(df_candles["fechamento"], length=20)
        df_candles["EMA_20"] = ema_20

        df_candles.ta.macd(close="fechamento", fast=12, slow=26, signal=9, append=True)

        df_candles["price_weighted"] = df_candles["fechamento"] * df_candles["volume"]
        df_candles["VWAP"] = (
            df_candles["price_weighted"].sum() / df_candles["volume"].sum()
        )

        print(f"RSI: {df_candles['rsi'].iloc[-1]}")
        print(f"EMA_20: {df_candles['EMA_20'].iloc[-1]}")
        print(f"MACD: {df_candles['MACD_12_26_9'].iloc[-1]}")
        print(f"VWAP: {df_candles['VWAP'].iloc[-1]}")
        print(f"Preço: {df_candles['fechamento'].iloc[-1]}")

        # condições de long e short
        price = helper.binance.fetch_trades(symbol, limit=1)[0]["price"]
        price = float(helper.binance.price_to_precision(symbol, price))

        if (
            df_candles["rsi"].iloc[-1] <= 30
            and price >= df_candles["EMA_20"].iloc[-1]
            and price >= df_candles["VWAP"].iloc[-1]
            and df_candles["MACD_12_26_9"].iloc[-1]
            >= df_candles["MACDs_12_26_9"].iloc[-1]
        ):
            if (
                not helper.has_exceeded_max_size(symbol, posicao_max)
                and helper.get_open_positions(symbol)[0] != "short"
                and not helper.is_last_order_open(symbol)
            ):
                try:
                    bid, ask = helper.get_order_book(symbol)
                    bid_price = helper.binance.price_to_precision(symbol, float(bid))
                    helper.binance.create_order(
                        symbol=symbol,
                        type="limit",
                        side="buy",
                        price=bid_price,
                        amount=posicao,
                        params={"hedged": True},
                    )

                    print(
                        f"Abrindo posição long em {bid_price}, tamanho {posicao}, par {symbol}"
                    )
                except Exception as e:
                    print(f"Erro ao abrir posição long: {e}")
        elif (
            df_candles["rsi"].iloc[-1] >= 70
            and price <= df_candles["EMA_20"].iloc[-1]
            and price <= df_candles["VWAP"].iloc[-1]
            and df_candles["MACD_12_26_9"].iloc[-1]
            <= df_candles["MACDs_12_26_9"].iloc[-1]
        ):
            if (
                not helper.has_exceeded_max_size(symbol, posicao_max)
                and helper.get_open_positions(symbol)[0] != "long"
                and not helper.is_last_order_open(symbol)
            ):
                try:
                    bid, ask = helper.get_order_book(symbol)
                    ask_price = helper.binance.price_to_precision(symbol, float(ask))
                    helper.binance.create_order(
                        symbol=symbol,
                        type="limit",
                        side="sell",
                        price=ask_price,
                        amount=posicao,
                        params={"hedged": True},
                    )

                    print(
                        f"Abrindo posição short em {ask_price}, tamanho {posicao}, par {symbol}"
                    )
                except Exception as e:
                    print(f"Erro ao abrir posição short: {e}")
        else:
            print("Nenhuma condição atendida para abrir posição")


if __name__ == "__main__":
    strategy = WeaponCandleStrategy()
    schedule.every(5).seconds.do(strategy.job)

    while True:
        try:
            schedule.run_pending()
        except Exception as e:
            print(f"Erro no loop principal: {e}")
            time.sleep(10)

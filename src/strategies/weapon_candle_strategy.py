import time

import pandas as pd
import schedule

from src.adapters.exchanges.binance.binance_futures_trading_adapter import (
    BinanceFuturesTradingAdapter,
)
from src.adapters.exchanges.interfaces.i_futures_trading_adapter import (
    IFuturesTradingAdapter,
)
from src.adapters.notification.messages.future_trading_messages import (
    FutureTradingMessages,
)
from src.adapters.notification.telegram.telegram_adapter import TelegramAdapter
from src.configs.logger_config import logger
from src.helpers.indicators_helper import IndicatorsHelper


class WeaponCandleStrategy:
    def __init__(
        self,
        notification_adapter: TelegramAdapter,
        futures_trading_adapter: IFuturesTradingAdapter,
        symbol: str = "BTCUSDT",
        load_candles_timeframe: str = "30m",
        load_candles_limit: int = 48,
        stop_loss: float = -4.0,
        profit_target: float = 8.0,
        max_position_size: float = 0.004,
        position_size: float = 0.002,
    ):
        self._notification_adapter = notification_adapter
        self._trading_adapter = futures_trading_adapter

        self._symbol = symbol
        self._load_candles_timeframe = load_candles_timeframe
        self._load_candles_limit = load_candles_limit
        self._stop_loss = stop_loss
        self._profit_target = profit_target
        self._max_position_size = max_position_size
        self._position_size = position_size

        logger.info(
            f"Strategy init: {self._symbol} TF={self._load_candles_timeframe}, "
            f"Stop={self._stop_loss}%, Target={self._profit_target}%, "
            f"MaxSize={self._max_position_size}, Size={self._position_size}"
        )

    def execute_strategy(self):
        logger.info(f"Executando estratégia para {self._symbol}...")
        self.close_allowed_positions()
        df_candles = self.load_candles()
        df_candles = self.calculate_indicators(df_candles)
        self.check_and_place_orders(df_candles)

    def close_allowed_positions(self):
        self._trading_adapter.close_allowed_positions(
            symbol=self._symbol, loss=self._stop_loss, target=self._profit_target
        )

    def load_candles(self) -> pd.DataFrame:
        df = self._trading_adapter.load_candles(
            symbol=self._symbol,
            timeframe=self._load_candles_timeframe,
            limit=self._load_candles_limit,
        )
        logger.info(f"Candles carregados para {self._symbol}.")
        return df

    def calculate_indicators(self, df: pd.DataFrame) -> pd.DataFrame:
        df["rsi"] = IndicatorsHelper.calculate_rsi(df)
        df["EMA_20"] = IndicatorsHelper.calculate_ema(df)
        IndicatorsHelper.calculate_macd(df)
        df["VWAP"] = IndicatorsHelper.calculate_vwap(df)
        logger.info(f"Indicadores calculados para {self._symbol}.")
        return df

    def check_and_place_orders(self, df: pd.DataFrame):
        try:
            price = self._trading_adapter.get_last_trade_price(self._symbol)
            if price is None:
                return

            rsi_val = df["rsi"].iloc[-1]
            ema_val = df["EMA_20"].iloc[-1]
            macd_val = df["MACD_12_26_9"].iloc[-1]
            macd_signal_val = df["MACDs_12_26_9"].iloc[-1]
            vwap_val = df["VWAP"].iloc[-1]
            price_val = df["close"].iloc[-1]

            if "close_time" in df.columns:
                close_time_str = str(df["close_time"].iloc[-1])
            else:
                close_time_str = pd.Timestamp.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")

            if self.can_open_long_position_by_strategy_rule(df, price):
                if self._trading_adapter.can_open_position_by_default_rule(
                    self._symbol, self._max_position_size, expected_side="long"
                ):
                    message = FutureTradingMessages.create_long_position_message(
                        symbol=self._symbol,
                        position_size=self._position_size,
                        stop_loss=self._stop_loss,
                        profit_target=self._profit_target,
                        timeframe=self._load_candles_timeframe,
                        limit=self._load_candles_limit,
                        close_time_str=close_time_str,
                        rsi_val=rsi_val,
                        ema_val=ema_val,
                        macd_val=macd_val,
                        macd_signal_val=macd_signal_val,
                        vwap_val=vwap_val,
                        price_val=price_val,
                    )
                    self._trading_adapter.open_position(
                        self._symbol, "long", self._position_size
                    )
                    self._notification_adapter.send_message(message)
                    logger.info(
                        f"Condições LONG atendidas, posição pode ser aberta em {self._symbol}."
                    )
                else:
                    logger.info(
                        f"Condições LONG atendidas, mas regras padrão vetam abertura em {self._symbol}."
                    )
            elif self.can_open_short_position_by_strategy(df, price):
                if self._trading_adapter.can_open_position_by_default_rule(
                    self._symbol, self._max_position_size, expected_side="short"
                ):
                    message = FutureTradingMessages.create_short_position_message(
                        symbol=self._symbol,
                        position_size=self._position_size,
                        stop_loss=self._stop_loss,
                        profit_target=self._profit_target,
                        timeframe=self._load_candles_timeframe,
                        limit=self._load_candles_limit,
                        close_time_str=close_time_str,
                        rsi_val=rsi_val,
                        ema_val=ema_val,
                        macd_val=macd_val,
                        macd_signal_val=macd_signal_val,
                        vwap_val=vwap_val,
                        price_val=price_val,
                    )
                    self._trading_adapter.open_position(
                        self._symbol, "short", self._position_size
                    )
                    self._notification_adapter.send_message(message)
                    logger.info(
                        f"Condições SHORT atendidas, posição pode ser aberta em {self._symbol}."
                    )
                else:
                    logger.info(
                        f"Condições SHORT atendidas, mas regras padrão vetam abertura em {self._symbol}."
                    )
            else:
                # Sem condições de entrada, menos log detalhado.
                logger.info(f"Nenhuma condição de entrada atendida em {self._symbol}.")
        except Exception as e:
            logger.error(
                f"Erro ao verificar condições de entrada para {self._symbol}: {e}"
            )

    def can_open_long_position_by_strategy_rule(
        self, df: pd.DataFrame, price: float
    ) -> bool:
        return (
            df["rsi"].iloc[-1] <= 30
            and price >= df["EMA_20"].iloc[-1]
            and price >= df["VWAP"].iloc[-1]
            and df["MACD_12_26_9"].iloc[-1] >= df["MACDs_12_26_9"].iloc[-1]
        )

    def can_open_short_position_by_strategy(
        self, df: pd.DataFrame, price: float
    ) -> bool:
        return (
            df["rsi"].iloc[-1] >= 70
            and price <= df["EMA_20"].iloc[-1]
            and price <= df["VWAP"].iloc[-1]
            and df["MACD_12_26_9"].iloc[-1] <= df["MACDs_12_26_9"].iloc[-1]
        )


if __name__ == "__main__":
    notification_adapter = TelegramAdapter()
    futures_trading_adapter = BinanceFuturesTradingAdapter(
        notification_adapter=notification_adapter
    )

    strategy = WeaponCandleStrategy(
        notification_adapter=notification_adapter,
        futures_trading_adapter=futures_trading_adapter,
        symbol="BTCUSDT",
        load_candles_timeframe="30m",
        load_candles_limit=48,
        stop_loss=-4,
        profit_target=8,
        max_position_size=0.004,
        position_size=0.002,
    )

    schedule.every(5).seconds.do(strategy.execute_strategy)

    while True:
        try:
            schedule.run_pending()
        except Exception as e:
            logger.error(f"Erro no loop principal: {e}")
            time.sleep(10)

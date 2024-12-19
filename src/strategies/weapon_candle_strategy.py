import time

import pandas as pd
import schedule

from src.helpers.binance.futures_trading_helper import BinanceFuturesTradingHelper
from src.helpers.indicators_helper import IndicatorsHelper


class WeaponCandleStrategy:
    """
    A trading strategy based on technical indicators such as RSI, EMA, MACD, and VWAP.
    """

    def __init__(
        self,
        symbol: str = "BTCUSDT",
        load_candles_timeframe: str = "30m",
        load_candles_limit: int = 48,
        stop_loss: float = -4.0,
        profit_target: float = 8.0,
        max_position_size: float = 0.004,
        position_size: float = 0.002,
    ):
        """
        Initialize the trading strategy.

        :param symbol: Trading pair symbol (e.g., "BTCUSDT").
        :param load_candles_timeframe: Timeframe for loading candle data (e.g., "30m").
        :param load_candles_limit: Number of candles to load for calculations.
        :param stop_loss: Stop-loss percentage.
        :param profit_target: Target profit percentage.
        :param max_position_size: Maximum allowable position size.
        :param position_size: Position size to open.
        """
        self.symbol = symbol
        self.load_candles_timeframe = load_candles_timeframe
        self.load_candles_limit = load_candles_limit
        self.stop_loss = stop_loss
        self.profit_target = profit_target
        self.max_position_size = max_position_size
        self.position_size = position_size

        self.helper = BinanceFuturesTradingHelper()

    def execute_strategy(self):
        """
        Executes the trading strategy by managing positions, loading candles, calculating indicators,
        and checking conditions for new orders.
        """
        print("Starting strategy execution...")

        self.clear_old_positions()

        df_candles = self.load_candles()
        df_candles = self.calculate_indicators(df_candles)

        self.check_and_place_orders(df_candles)

        print("Strategy execution completed.\n")

    def clear_old_positions(self):
        """
        Clears old positions based on loss and target thresholds.
        """
        self.helper.clear_old_positions(
            symbol=self.symbol, loss=self.stop_loss, target=self.profit_target
        )

    def load_candles(self) -> pd.DataFrame:
        """
        Loads the candle data.

        :return: A DataFrame containing the candle data.
        """
        print("Loading candles...")
        return self.helper.load_candles(
            symbol=self.symbol,
            timeframe=self.load_candles_timeframe,
            limit=self.load_candles_limit,
        )

    def calculate_indicators(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Calculates the required technical indicators and logs their values.

        :param df: A DataFrame containing the candle data.
        :return: A DataFrame containing the candle data with calculated indicators.
        """
        print("Calculating technical indicators...")
        df["rsi"] = IndicatorsHelper.calculate_rsi(df)
        df["EMA_20"] = IndicatorsHelper.calculate_ema(df)
        IndicatorsHelper.calculate_macd(df)
        df["VWAP"] = IndicatorsHelper.calculate_vwap(df)
        print("Indicators successfully calculated.")

        # Log indicators
        print(f"RSI: {df['rsi'].iloc[-1]}")
        print(f"EMA_20: {df['EMA_20'].iloc[-1]}")
        print(f"MACD: {df['MACD_12_26_9'].iloc[-1]}")
        print(f"MACD Signal: {df['MACDs_12_26_9'].iloc[-1]}")
        print(f"VWAP: {df['VWAP'].iloc[-1]}")
        print(f"Price: {df['close'].iloc[-1]}")

        return df

    def check_and_place_orders(self, df: pd.DataFrame):
        """
        Checks the conditions for entering new orders (long or short) and places orders if conditions are met.

        :param df: A DataFrame containing the candle data and indicators.
        """
        try:
            price = self.helper.get_last_trade_price(self.symbol)
            if price is None:
                return

            if self.can_open_long_position_by_strategy_rule(df, price):
                print("LONG entry conditions met.")
                if self.helper.can_open_position_by_default_rule(
                    self.symbol, self.max_position_size, expected_side="long"
                ):
                    pass
                    # Uncomment to open position:
                    # self.helper.open_position(self.symbol, "long", self.position_size)
            elif self.can_open_short_position_by_strategy(df, price):
                print("SHORT entry conditions met.")
                if self.helper.can_open_position_by_default_rule(
                    self.symbol, self.max_position_size, expected_side="short"
                ):
                    pass
                    # Uncomment to open position:
                    # self.helper.open_position(self.symbol, "short", self.position_size)
            else:
                print("No entry conditions met.")
                # Call the function to print differences
                self.print_indicator_differences(df, price)
        except Exception as e:
            print(f"Error checking entry conditions: {e}")

    def print_indicator_differences(self, df: pd.DataFrame, price: float):
        """
        Prints the differences between the current indicators and what would be needed to meet
        the conditions for short and long entries.
        """
        rsi = df["rsi"].iloc[-1]
        ema = df["EMA_20"].iloc[-1]
        vwap = df["VWAP"].iloc[-1]
        macd = df["MACD_12_26_9"].iloc[-1]
        macd_signal = df["MACDs_12_26_9"].iloc[-1]

        # Conditions for LONG:
        # RSI <= 30, price >= EMA, price >= VWAP, MACD >= MACD Signal
        # For each condition, calculate how much adjustment is needed if it's not met:
        diff_rsi_long = (rsi - 30) if rsi > 30 else 0.0  # How much RSI must decrease
        diff_ema_long = (
            (ema - price) if price < ema else 0.0
        )  # How much price must increase to reach EMA
        diff_vwap_long = (
            (vwap - price) if price < vwap else 0.0
        )  # How much price must increase to reach VWAP
        diff_macd_long = (
            (macd_signal - macd) if macd < macd_signal else 0.0
        )  # How much MACD must increase

        # Conditions for SHORT:
        # RSI >= 70, price <= EMA, price <= VWAP, MACD <= MACD Signal
        diff_rsi_short = (70 - rsi) if rsi < 70 else 0.0  # How much RSI must increase
        diff_ema_short = (
            (price - ema) if price > ema else 0.0
        )  # How much price must decrease to reach EMA
        diff_vwap_short = (
            (price - vwap) if price > vwap else 0.0
        )  # How much price must decrease to reach VWAP
        diff_macd_short = (
            (macd - macd_signal) if macd > macd_signal else 0.0
        )  # How much MACD must decrease

        print("Differences needed to meet LONG conditions:")
        print(f"RSI must decrease by: {diff_rsi_long:.4f}")
        print(f"Price must increase by: {diff_ema_long:.4f} to reach EMA")
        print(f"Price must increase by: {diff_vwap_long:.4f} to reach VWAP")
        print(f"MACD must increase by: {diff_macd_long:.4f}")

        print("Differences needed to meet SHORT conditions:")
        print(f"RSI must increase by: {diff_rsi_short:.4f}")
        print(f"Price must decrease by: {diff_ema_short:.4f} to reach EMA")
        print(f"Price must decrease by: {diff_vwap_short:.4f} to reach VWAP")
        print(f"MACD must decrease by: {diff_macd_short:.4f}")

    def can_open_long_position_by_strategy_rule(
        self, df: pd.DataFrame, price: float
    ) -> bool:
        """
        Determines if a long position can be opened based on strategy conditions.

        :param df: A DataFrame containing the candle data and indicators.
        :param price: The current market price.
        :return: True if a long position can be opened, False otherwise.
        """
        return (
            df["rsi"].iloc[-1] <= 30
            and price >= df["EMA_20"].iloc[-1]
            and price >= df["VWAP"].iloc[-1]
            and df["MACD_12_26_9"].iloc[-1] >= df["MACDs_12_26_9"].iloc[-1]
        )

    def can_open_short_position_by_strategy(
        self, df: pd.DataFrame, price: float
    ) -> bool:
        """
        Determines if a short position can be opened based on strategy conditions.

        :param df: A DataFrame containing the candle data and indicators.
        :param price: The current market price.
        :return: True if a short position can be opened, False otherwise.
        """
        return (
            df["rsi"].iloc[-1] >= 70
            and price <= df["EMA_20"].iloc[-1]
            and price <= df["VWAP"].iloc[-1]
            and df["MACD_12_26_9"].iloc[-1] <= df["MACDs_12_26_9"].iloc[-1]
        )


if __name__ == "__main__":
    strategy = WeaponCandleStrategy(
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
            time.sleep(1)
        except Exception as e:
            print(f"Error in main loop: {e}")
            time.sleep(10)

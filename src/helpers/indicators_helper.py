import pandas as pd
import pandas_ta as ta
from ta.momentum import RSIIndicator


class IndicatorsHelper:
    """
    A class responsible for calculating technical indicators.

    Provides static methods to calculate:
    - RSI (Relative Strength Index)
    - EMA (Exponential Moving Average)
    - MACD (Moving Average Convergence Divergence)
    - VWAP (Volume Weighted Average Price)
    - SMA (Simple Moving Average)
    - Support and Resistance levels
    """

    @staticmethod
    def calculate_rsi(df: pd.DataFrame, period: int = 14) -> pd.Series:
        """
        Calculates the RSI (Relative Strength Index).

        :param df: A DataFrame containing candles with a 'close' column.
        :param period: The period for RSI calculation.
        :return: A Series containing RSI values.
        """
        rsi = RSIIndicator(df["close"], window=period)
        return rsi.rsi()

    @staticmethod
    def calculate_ema(df: pd.DataFrame, period: int = 20) -> pd.Series:
        """
        Calculates the EMA (Exponential Moving Average) for a specified period.

        :param df: A DataFrame containing candles with a 'close' column.
        :param period: The period for EMA calculation.
        :return: A Series containing EMA values.
        """
        return ta.ema(df["close"], length=period)

    @staticmethod
    def calculate_macd(
        df: pd.DataFrame, fast: int = 12, slow: int = 26, signal: int = 9
    ) -> pd.DataFrame:
        """
        Calculates the MACD (Moving Average Convergence Divergence).

        :param df: A DataFrame containing candles with a 'close' column.
        :param fast: The fast EMA period.
        :param slow: The slow EMA period.
        :param signal: The signal EMA period.
        :return: A DataFrame with columns:
                 - MACD_12_26_9
                 - MACDs_12_26_9 (signal line)
                 - MACDh_12_26_9 (histogram)
        """
        return df.ta.macd(
            close="close", fast=fast, slow=slow, signal=signal, append=True
        )

    @staticmethod
    def calculate_vwap(df: pd.DataFrame) -> pd.Series:
        """
        Calculates a simplified VWAP (Volume Weighted Average Price).

        :param df: A DataFrame containing candles with 'close' and 'volume' columns.
        :return: A Series containing VWAP values, replicated for all rows in the same window.
        """
        df["price_weighted"] = df["close"] * df["volume"]
        vwap_value = df["price_weighted"].sum() / df["volume"].sum()
        # Returns a Series with the VWAP value replicated for all rows
        return pd.Series([vwap_value] * len(df), index=df.index)

    @staticmethod
    def calculate_sma(df: pd.DataFrame, period: int = 20) -> pd.Series:
        """
        Calculates the SMA (Simple Moving Average) for a specified period.

        :param df: A DataFrame containing candles with a 'close' column.
        :param period: The period for SMA calculation.
        :return: A Series containing SMA values.
        """
        return ta.sma(df["close"], length=period)

    @staticmethod
    def calculate_support_resistance(
        df: pd.DataFrame, window: int = 10
    ) -> pd.DataFrame:
        """
        Calculates support and resistance levels using the minimum and maximum of the last 'window' candles.

        :param df: A DataFrame containing candles with 'low' and 'high' columns.
        :param window: The number of candles to consider for the calculation.
        :return: A DataFrame with 'support' and 'resistance' columns.
        """
        df["support"] = df["low"].rolling(window).min()
        df["resistance"] = df["high"].rolling(window).max()
        return df

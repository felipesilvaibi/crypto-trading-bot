import decimal
from abc import ABC, abstractmethod
from typing import Optional, Tuple

import pandas as pd


class IFuturesTradingAdapter(ABC):
    @abstractmethod
    def get_open_positions(
        self, symbol: str
    ) -> Tuple[
        Optional[str],
        Optional[float],
        Optional[float],
        bool,
        Optional[float],
        Optional[float],
        Optional[float],
    ]:
        """
        Fetches the open position for the given symbol.
        """
        pass

    @abstractmethod
    def get_order_book(self, symbol: str) -> Tuple[decimal.Decimal, decimal.Decimal]:
        """
        Fetches the order book for the given symbol.
        """
        pass

    @abstractmethod
    def close_position(self, symbol: str) -> None:
        """
        Closes the current position for the given symbol.
        """
        pass

    @abstractmethod
    def close_pnl_position(self, symbol: str, loss: float, target: float) -> None:
        """
        Closes a position based on profit or loss thresholds.
        """
        pass

    @abstractmethod
    def has_exceeded_max_size(self, symbol: str, max_size: float) -> bool:
        """
        Checks if the current position size exceeds the maximum allowed size.
        """
        pass

    @abstractmethod
    def is_last_order_open(self, symbol: str) -> bool:
        """
        Checks if there is a pending open order for the given symbol.
        """
        pass

    @abstractmethod
    def load_candles(
        self, symbol: str, timeframe: str, limit: int = 48
    ) -> pd.DataFrame:
        """
        Loads candlestick data (OHLCV) for the given symbol and timeframe.
        """
        pass

    @abstractmethod
    def close_allowed_positions(self, symbol: str, loss: float, target: float) -> None:
        """
        Clears old positions and cancels all open orders.
        """
        pass

    @abstractmethod
    def can_open_position_by_default_rule(
        self, symbol: str, max_size: float, expected_side: str
    ) -> bool:
        """
        Checks if a new position can be opened based on default rules.
        """
        pass

    @abstractmethod
    def get_last_trade_price(self, symbol: str) -> Optional[float]:
        """
        Fetches the last traded price for the given symbol.
        """
        pass

    @abstractmethod
    def open_position(self, symbol: str, side: str, amount: float) -> None:
        """
        Opens a new position for the given symbol.
        """
        pass

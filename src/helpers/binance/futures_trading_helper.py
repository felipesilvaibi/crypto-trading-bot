import decimal
import os
import time
from typing import Optional, Tuple

import ccxt
import pandas as pd
from dotenv import load_dotenv

load_dotenv()


class BinanceFuturesTradingHelper:
    """
    Helper class to interact with Binance Futures using the ccxt library.

    This class provides methods for:
    - Loading candlestick data (OHLCV).
    - Managing positions, orders, stop-loss, and take-profit.
    - Checking environment constraints (maximum size, open orders, opposite positions).
    - Fetching the latest traded price.
    - Opening new positions.
    """

    def __init__(self) -> None:
        """
        Initializes the Binance Futures API client using environment variables for authentication.
        """
        self.binance = ccxt.binance(
            {
                "enableRateLimit": True,
                "options": {"defaultType": "future"},
                "apiKey": os.getenv("BINANCE_API_KEY"),
                "secret": os.getenv("BINANCE_API_SECRET"),
            }
        )

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

        :param symbol: The trading pair symbol (e.g., "BTCUSDT").
        :return: A tuple containing position details (side, size, entry price, position open status, notional, percentage change, PnL).
        """
        positions = self.binance.fetch_positions(symbols=[symbol])
        for position in positions:
            side = position["side"]
            size = float(position["info"]["positionAmt"].replace("-", ""))
            entry_price = float(position["entryPrice"])
            notional = float(position["notional"])
            percentage = float(position["percentage"])
            pnl = float(position["info"]["unRealizedProfit"])

            position_open = side in ["long", "short"]
            return side, size, entry_price, position_open, notional, percentage, pnl

        return None, None, None, False, None, None, None

    def get_order_book(self, symbol: str) -> Tuple[decimal.Decimal, decimal.Decimal]:
        """
        Fetches the order book for the given symbol.

        :param symbol: The trading pair symbol (e.g., "BTCUSDT").
        :return: A tuple containing the best bid and ask prices.
        """
        order_book = self.binance.fetch_order_book(symbol)
        bid = decimal.Decimal(order_book["bids"][0][0])
        ask = decimal.Decimal(order_book["asks"][0][0])
        return bid, ask

    def close_position(self, symbol: str) -> None:
        """
        Closes the current position for the given symbol.

        :param symbol: The trading pair symbol (e.g., "BTCUSDT").
        """
        print(f"Starting position close for {symbol}...")
        while True:
            position_data = self.get_open_positions(symbol)
            side, size, _, position_open, _, _, _ = position_data

            if not position_open:
                print("No open positions found, closing process completed.")
                break

            self.binance.cancel_all_orders(symbol)
            bid, ask = self.get_order_book(symbol)

            if side == "long":
                print("Closing long position.")
                ask_price = self.binance.price_to_precision(symbol, float(ask))
                self.binance.create_order(
                    symbol=symbol,
                    type="limit",
                    side="sell",
                    price=ask_price,
                    amount=size,
                    params={"hedged": True},
                )
                print(f"Sell close order created at {ask_price}")
            elif side == "short":
                print("Closing short position.")
                bid_price = self.binance.price_to_precision(symbol, float(bid))
                self.binance.create_order(
                    symbol=symbol,
                    type="limit",
                    side="buy",
                    price=bid_price,
                    amount=size,
                    params={"hedged": True},
                )
                print(f"Buy close order created at {bid_price}")

            time.sleep(20)

    def close_pnl_position(self, symbol: str, loss: float, target: float) -> None:
        """
        Closes a position based on profit or loss thresholds.

        :param symbol: The trading pair symbol (e.g., "BTCUSDT").
        :param loss: Stop-loss percentage.
        :param target: Take-profit percentage.
        """
        _, _, _, _, _, percent, pnl = self.get_open_positions(symbol)
        if percent is not None:
            if percent < loss:
                print(f"Stop-loss reached ({percent}%), closing position.")
                self.close_position(symbol)
                print(f"Position closed due to stop-loss: PnL={pnl}")
            elif percent >= target:
                print(f"Take-profit reached ({percent}%), closing position.")
                self.close_position(symbol)
                print(f"Position closed due to take-profit: PnL={pnl}")

    def has_exceeded_max_size(self, symbol: str, max_size: float) -> bool:
        """
        Checks if the current position size exceeds the maximum allowed size.

        :param symbol: The trading pair symbol (e.g., "BTCUSDT").
        :param max_size: Maximum allowable position size.
        :return: True if the current position size exceeds the maximum, False otherwise.
        """
        _, size, _, _, _, _, _ = self.get_open_positions(symbol)
        if size and size >= max_size:
            print(
                f"Current position size ({size}) exceeds the maximum allowed ({max_size})."
            )
            return True
        return False

    def is_last_order_open(self, symbol: str) -> bool:
        """
        Checks if there is a pending open order for the given symbol.

        :param symbol: The trading pair symbol (e.g., "BTCUSDT").
        :return: True if there is a pending open order, False otherwise.
        """
        open_orders = self.binance.fetch_orders(symbol)
        if not open_orders:
            return False
        last_order_status = open_orders[-1]["status"]
        if last_order_status == "open":
            print("There is a pending open order.")
        return last_order_status == "open"

    def load_candles(
        self, symbol: str, timeframe: str, limit: int = 48
    ) -> pd.DataFrame:
        """
        Loads candlestick data (OHLCV) for the given symbol and timeframe.

        :param symbol: The trading pair symbol (e.g., "BTCUSDT").
        :param timeframe: Timeframe for the candles (e.g., "1h").
        :param limit: Number of candles to fetch.
        :return: A DataFrame containing OHLCV data.
        """
        print(f"Loading {limit} candles for {symbol} with timeframe {timeframe}...")
        bars = self.binance.fetch_ohlcv(symbol, timeframe, limit=limit)
        df = pd.DataFrame(
            bars, columns=["time", "open", "high", "low", "close", "volume"]
        )
        df["time"] = pd.to_datetime(df["time"], unit="ms", utc=True).map(
            lambda x: x.tz_convert("America/Sao_Paulo")
        )
        print("Candles successfully loaded.")
        return df

    def clear_old_positions(self, symbol: str, loss: float, target: float) -> None:
        """
        Clears old positions and cancels all open orders.

        :param symbol: The trading pair symbol (e.g., "BTCUSDT").
        :param loss: Stop-loss percentage.
        :param target: Take-profit percentage.
        """
        print("Clearing old positions and orders...")
        try:
            self.binance.cancel_all_orders(symbol=symbol)
            print("All open orders have been canceled.")

            self.close_pnl_position(symbol=symbol, loss=loss, target=target)
        except Exception as e:
            print(f"Error managing positions: {e}")

    def can_open_position_by_default_rule(
        self, symbol: str, max_size: float, expected_side: str
    ) -> bool:
        """
        Checks if a new position can be opened based on default rules.

        :param symbol: The trading pair symbol (e.g., "BTCUSDT").
        :param max_size: Maximum allowable position size.
        :param expected_side: Expected side of the new position ("long" or "short").
        :return: True if the new position can be opened, False otherwise.
        """
        if self.has_exceeded_max_size(symbol, max_size):
            return False

        current_side = self.get_open_positions(symbol)[0]
        if expected_side == "long" and current_side == "short":
            print("A short position is already open, cannot open a long position now.")
            return False
        if expected_side == "short" and current_side == "long":
            print("A long position is already open, cannot open a short position now.")
            return False

        if self.is_last_order_open(symbol):
            print("There are pending open orders, cannot open a new position.")
            return False

        return True

    def get_last_trade_price(self, symbol: str) -> Optional[float]:
        """
        Fetches the last traded price for the given symbol.

        :param symbol: The trading pair symbol (e.g., "BTCUSDT").
        :return: The last traded price, or None if unavailable.
        """
        trades = self.binance.fetch_trades(symbol, limit=1)
        if not trades:
            print("Unable to fetch the last price, no recent trades found.")
            return None
        price = float(self.binance.price_to_precision(symbol, trades[0]["price"]))
        print(f"Last traded price: {price}")
        return price

    def open_position(self, symbol: str, side: str, amount: float) -> None:
        """
        Opens a new position for the given symbol.

        :param symbol: The trading pair symbol (e.g., "BTCUSDT").
        :param side: Position side ("long" or "short").
        :param amount: Position size.
        """
        print(f"Opening a {side} position for {symbol}...")
        try:
            bid, ask = self.get_order_book(symbol)
            if side == "long":
                bid_price = self.binance.price_to_precision(symbol, float(bid))
                self.binance.create_order(
                    symbol=symbol,
                    type="limit",
                    side="buy",
                    price=bid_price,
                    amount=amount,
                    params={"hedged": True},
                )
                print(f"LONG position opened at {bid_price}, size {amount}")
            elif side == "short":
                ask_price = self.binance.price_to_precision(symbol, float(ask))
                self.binance.create_order(
                    symbol=symbol,
                    type="limit",
                    side="sell",
                    price=ask_price,
                    amount=amount,
                    params={"hedged": True},
                )
                print(f"SHORT position opened at {ask_price}, size {amount}")
        except Exception as e:
            print(f"Error opening {side} position: {e}")

import decimal
import os
import time
from typing import Optional, Tuple

import ccxt
from dotenv import load_dotenv

load_dotenv()


class BinanceFuturesTradingHelper:
    """
    Helper class for trading with Binance Futures using the ccxt library.
    """

    def __init__(self) -> None:
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
        Fetches open position details for a given symbol.

        :param symbol: Trading pair symbol (e.g., "XRPUSDT").
        :return: Tuple containing side, size, entry price, position open status,
                 notional value, percentage change, and unrealized profit.
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
        Retrieves the order book for a given symbol.

        :param symbol: Trading pair symbol.
        :return: Tuple containing the highest bid and lowest ask prices.
        """
        order_book = self.binance.fetch_order_book(symbol)
        bid = decimal.Decimal(order_book["bids"][0][0])
        ask = decimal.Decimal(order_book["asks"][0][0])
        return bid, ask

    def close_position(self, symbol: str) -> None:
        """
        Closes an open position for the given symbol.

        :param symbol: Trading pair symbol.
        """
        while True:
            position_data = self.get_open_positions(symbol)
            side, size, _, position_open, _, _, _ = position_data

            if not position_open:
                break

            self.binance.cancel_all_orders(symbol)
            bid, ask = self.get_order_book(symbol)

            if side == "long":
                ask_price = self.binance.price_to_precision(symbol, float(ask))
                self.binance.create_order(
                    symbol=symbol,
                    type="limit",
                    side="sell",
                    price=ask_price,
                    amount=size,
                    params={"hedged": True},
                )
            elif side == "short":
                bid_price = self.binance.price_to_precision(symbol, float(bid))
                self.binance.create_order(
                    symbol=symbol,
                    type="limit",
                    side="buy",
                    price=bid_price,
                    amount=size,
                    params={"hedged": True},
                )

            time.sleep(20)

    def close_pnl_position(self, symbol: str, loss: float, target: float) -> None:
        """
        Monitors and manages open positions based on PnL targets.

        :param symbol: Trading pair symbol.
        :param loss: Stop-loss percentage.
        :param target: Take-profit percentage.
        """
        _, _, _, _, _, percent, pnl = self.get_open_positions(symbol)

        if percent is not None:
            if percent < loss:
                self.close_position(symbol)
                print(f"Position closed due to stop loss: {pnl}")
            elif percent >= target:
                self.close_position(symbol)
                print(f"Position closed due to take profit: {pnl}")

    def has_exceeded_max_size(self, symbol: str, max_size: float) -> bool:
        """
        Checks if the current position size exceeds the specified limit.

        :param symbol: Trading pair symbol.
        :param max_size: Maximum allowed size for a position.
        :return: True if the position size exceeds the limit, otherwise False.
        """
        _, size, _, _, _, _, _ = self.get_open_positions(symbol)
        return size >= max_size if size else False

    def is_last_order_open(self, symbol: str) -> bool:
        """
        Checks if the last order is still open.

        :param symbol: Trading pair symbol.
        :return: True if the last order is open, otherwise False.
        """
        open_orders = self.binance.fetch_orders(symbol)
        if not open_orders:
            return False

        last_order_status = open_orders[-1]["status"]
        return last_order_status == "open"

import decimal
import os
import time
from typing import Optional, Tuple

import ccxt
import pandas as pd
from dotenv import load_dotenv

from src.adapters.exchanges.interfaces.i_futures_trading_adapter import (
    IFuturesTradingAdapter,
)
from src.adapters.notification.interfaces.i_notification_adapter import (
    INotificationAdapter,
)
from src.adapters.notification.messages.future_trading_messages import (
    FutureTradingMessages,
)
from src.configs.logger_config import logger

load_dotenv()


class BinanceFuturesTradingAdapter(IFuturesTradingAdapter):
    def __init__(self, notification_adapter: INotificationAdapter) -> None:
        self.binance = ccxt.binance(
            {
                "enableRateLimit": True,
                "options": {"defaultType": "future"},
                "apiKey": os.getenv("BINANCE_API_KEY"),
                "secret": os.getenv("BINANCE_API_SECRET"),
            }
        )
        self._notifier = notification_adapter

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
        positions = self.binance.fetch_positions(symbols=[symbol])
        for position in positions:
            side = position["side"]
            size = (
                float(position["info"]["positionAmt"].replace("-", ""))
                if position["info"]["positionAmt"]
                else 0.0
            )
            entry_price = float(position["entryPrice"])
            notional = float(position["notional"])
            percentage = float(position["percentage"])
            pnl = float(position["info"]["unRealizedProfit"])
            position_open = side in ["long", "short"]
            return side, size, entry_price, position_open, notional, percentage, pnl

        return None, None, None, False, None, None, None

    def get_order_book(self, symbol: str) -> Tuple[decimal.Decimal, decimal.Decimal]:
        order_book = self.binance.fetch_order_book(symbol)
        bid = decimal.Decimal(order_book["bids"][0][0])
        ask = decimal.Decimal(order_book["asks"][0][0])
        return bid, ask

    def close_position(self, symbol: str) -> None:
        logger.info(f"Fechando posição para {symbol}...")
        while True:
            side, size, _, position_open, _, _, _ = self.get_open_positions(symbol)
            if not position_open:
                logger.info(f"Nenhuma posição aberta em {symbol}.")
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

            logger.info("Aguardando execução da ordem de fechamento...")
            time.sleep(20)

    def close_pnl_position(self, symbol: str, loss: float, target: float) -> None:
        side, size, entry_price, position_open, _, percent, pnl = (
            self.get_open_positions(symbol)
        )
        if percent is not None and position_open:
            percent_rounded = round(percent, 2)
            pnl_rounded = round(pnl, 2)
            size_rounded = round(size, 4) if size else 0.0
            entry_price_rounded = round(entry_price, 2) if entry_price else 0.0

            if percent_rounded < loss:
                logger.info(
                    f"[STOP-LOSS] {symbol}: {percent_rounded}%. Fechando posição..."
                )
                self.close_position(symbol)
                message = FutureTradingMessages.create_stop_loss_message(
                    symbol=symbol,
                    side=side,
                    size=size_rounded,
                    entry_price=entry_price_rounded,
                    pnl=pnl_rounded,
                    percent=percent_rounded,
                )
                self._notifier.send_message(message)

            elif percent_rounded >= target:
                logger.info(
                    f"[TAKE-PROFIT] {symbol}: {percent_rounded}%. Fechando posição..."
                )
                self.close_position(symbol)
                message = FutureTradingMessages.create_take_profit_message(
                    symbol=symbol,
                    side=side,
                    size=size_rounded,
                    entry_price=entry_price_rounded,
                    pnl=pnl_rounded,
                    percent=percent_rounded,
                )
                self._notifier.send_message(message)

    def has_exceeded_max_size(self, symbol: str, max_size: float) -> bool:
        _, size, _, _, _, _, _ = self.get_open_positions(symbol)
        if size and size >= max_size:
            logger.info(f"{symbol}: tamanho {size} excede máximo {max_size}.")
            return True
        return False

    def is_last_order_open(self, symbol: str) -> bool:
        open_orders = self.binance.fetch_orders(symbol)
        if not open_orders:
            return False
        return open_orders[-1]["status"] == "open"

    def load_candles(
        self, symbol: str, timeframe: str, limit: int = 48
    ) -> pd.DataFrame:
        df = self.binance.fetch_ohlcv(symbol, timeframe, limit=limit)
        df = pd.DataFrame(
            df, columns=["time", "open", "high", "low", "close", "volume"]
        )
        df["time"] = pd.to_datetime(df["time"], unit="ms", utc=True).map(
            lambda x: x.tz_convert("America/Sao_Paulo")
        )
        return df

    def close_allowed_positions(self, symbol: str, loss: float, target: float) -> None:
        try:
            self.binance.cancel_all_orders(symbol=symbol)
            self.close_pnl_position(symbol=symbol, loss=loss, target=target)
        except Exception as e:
            logger.error(f"Erro ao gerenciar posições para {symbol}: {e}")

    def can_open_position_by_default_rule(
        self, symbol: str, max_size: float, expected_side: str
    ) -> bool:
        if self.has_exceeded_max_size(symbol, max_size):
            return False

        current_side = self.get_open_positions(symbol)[0]
        if (expected_side == "long" and current_side == "short") or (
            expected_side == "short" and current_side == "long"
        ):
            return False

        if self.is_last_order_open(symbol):
            return False

        return True

    def get_last_trade_price(self, symbol: str) -> Optional[float]:
        trades = self.binance.fetch_trades(symbol, limit=1)
        if not trades:
            return None
        price = float(self.binance.price_to_precision(symbol, trades[0]["price"]))
        return price

    def open_position(self, symbol: str, side: str, amount: float) -> None:
        logger.info(f"Abrindo posição {side.upper()} em {symbol}, size={amount}...")
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
        except Exception as e:
            logger.error(f"Erro ao abrir posição {side.upper()} em {symbol}: {e}")

class FutureTradingMessages:
    """
    A helper class to construct formatted trading messages for notifications.
    """

    @staticmethod
    def create_long_position_message(
        symbol: str,
        position_size: float,
        stop_loss: float,
        profit_target: float,
        timeframe: str,
        limit: int,
        close_time_str: str,
        rsi_val: float,
        ema_val: float,
        macd_val: float,
        macd_signal_val: float,
        vwap_val: float,
        price_val: float,
    ) -> str:
        """
        Constructs a message for a long position.
        """
        return (
            f"\U0001f4c8 *Long position opened* \U0001f4c8 \n\n"
            "*Position:*\n"
            f"• *Pair*: `{symbol}`\n"
            f"• *Size*: `{position_size}`\n"
            f"• *Stop\-Loss*: `{stop_loss}`%\n"
            f"• *Profit\-Target*: `{profit_target}%`\n"
            f"• *Timeframe*: `{timeframe}`\n"
            f"• *Limit*: `{limit}`\n\n"
            "*Indicators:*\n"
            f"• *date*: `{close_time_str}`\n"
            f"• *RSI*: `{rsi_val:.2f}`\n"
            f"• *EMA\_20*: `{ema_val:.2f}`\n"
            f"• *MACD*: `{macd_val:.2f}`\n"
            f"• *MACD\_Signal*: `{macd_signal_val:.2f}`\n"
            f"• *VWAP*: `{vwap_val:.2f}`\n"
            f"• *Price*: `{price_val:.2f}`"
        )

    @staticmethod
    def create_short_position_message(
        symbol: str,
        position_size: float,
        stop_loss: float,
        profit_target: float,
        timeframe: str,
        limit: int,
        close_time_str: str,
        rsi_val: float,
        ema_val: float,
        macd_val: float,
        macd_signal_val: float,
        vwap_val: float,
        price_val: float,
    ) -> str:
        """
        Constructs a message for a short position.
        """
        return (
            f"\U0001f4c9 *Short position opened* \U0001f4c9\n\n"
            "*Position:*\n"
            f"• *Pair*: `{symbol}`\n"
            f"• *Size*: `{position_size}`\n"
            f"• *Stop\-Loss*: `{stop_loss}`%\n"
            f"• *Profit\-Target*: `{profit_target}%`\n"
            f"• *Timeframe*: `{timeframe}`\n"
            f"• *Limit*: `{limit}`\n\n"
            "*Indicators:*\n"
            f"• *date*: `{close_time_str}`\n"
            f"• *RSI*: `{rsi_val:.2f}`\n"
            f"• *EMA\_20*: `{ema_val:.2f}`\n"
            f"• *MACD*: `{macd_val:.2f}`\n"
            f"• *MACD\_Signal*: `{macd_signal_val:.2f}`\n"
            f"• *VWAP*: `{vwap_val:.2f}`\n"
            f"• *Price*: `{price_val:.2f}`"
        )

    @staticmethod
    def create_stop_loss_message(
        symbol: str,
        side: str,
        size: float,
        entry_price: float,
        pnl: float,
        percent: float,
    ) -> str:
        """
        Constructs a message for a stop-loss trigger.
        """
        return (
            "\U0001f534 *STOP\-LOSS TRIGGERED* \U0001f534\n\n"
            f"*Symbol*: `{symbol}`\n"
            f"*Side*: `{side}`\n"
            f"*Size*: `{size}`\n"
            f"*Entry Price*: `{entry_price}`\n"
            f"*PnL*: `{pnl}`\n"
            f"*Return*: `{percent}%`\n\n"
            "*Position closed due to stop\-loss.*"
        )

    @staticmethod
    def create_take_profit_message(
        symbol: str,
        side: str,
        size: float,
        entry_price: float,
        pnl: float,
        percent: float,
    ) -> str:
        """
        Constructs a message for a take-profit trigger.
        """
        return (
            "\U0001f7e2 *TAKE\-PROFIT TRIGGERED* \U0001f7e2\n\n"
            f"*Symbol*: `{symbol}`\n"
            f"*Side*: `{side}`\n"
            f"*Size*: `{size}`\n"
            f"*Entry Price*: `{entry_price}`\n"
            f"*PnL*: `{pnl}`\n"
            f"*Return*: `{percent}%`\n\n"
            "*Position closed due to take\-profit.*"
        )

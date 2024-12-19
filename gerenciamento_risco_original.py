import decimal
import os
import time

import ccxt
from dotenv import load_dotenv

load_dotenv()

binance_api_key = os.getenv("BINANCE_API_KEY")
binance_api_secret = os.getenv("BINANCE_API_SECRET")


binance = ccxt.binance(
    {
        "enableRateLimit": True,
        "options": {"defaultType": "future"},
        "apiKey": binance_api_key,
        "secret": binance_api_secret,
    }
)

symbols = ["XRPUSDT"]
bal = binance.fetch_positions(symbols=symbols)


def posicoes_abertas(symbol):
    lado = []
    tamanho = []
    preco_entrada = []
    notional = []
    percentage = []
    pnl = []

    bal = binance.fetch_positions(symbols=[symbol])
    for i in bal:
        lado = i["side"]
        tamanho = i["info"]["positionAmt"].replace("-", "")
        preco_entrada = i["entryPrice"]
        notional = i["notional"]
        percentage = i["percentage"]
        pnl = i["info"]["unRealizedProfit"]

    if lado in ["long", "short"]:
        pos_aberta = True
    else:
        pos_aberta = False

    return lado, tamanho, preco_entrada, pos_aberta, notional, percentage, pnl


def livro_ofertas(symbol):
    livro_ofertas = binance.fetch_order_book(symbol)
    bid = decimal.Decimal(livro_ofertas["bids"][0][0])
    ask = decimal.Decimal(livro_ofertas["asks"][0][0])
    return bid, ask


def encerra_posicao(symbol):
    pos_aberta = posicoes_abertas(symbol)[3]
    while pos_aberta:
        posicoes_abertas_var = posicoes_abertas(symbol)
        lado = posicoes_abertas_var[0]
        tamanho = posicoes_abertas_var[1]

        if lado == "long":
            binance.cancel_all_orders(symbol)
            bid, ask = livro_ofertas(symbol)
            ask = binance.price_to_precision(symbol, ask)
            binance.create_order(
                symbol=symbol,
                type="limit",
                side="sell",
                price=ask,
                amount=tamanho,
                params={"hedged": True},
            )
            # msg = "Vendendo posição..."
            # telegram
            time.sleep(20)

        elif lado == "short":
            binance.cancel_all_orders(symbol)
            bid, ask = livro_ofertas(symbol)
            bid = binance.price_to_precision(symbol, bid)
            binance.create_order(
                symbol=symbol,
                type="limit",
                side="buy",
                price=bid,
                amount=tamanho,
                params={"hedged": True},
            )
            time.sleep(20)

        if not posicoes_abertas_var[3]:
            pos_aberta = False


def fecha_pnl(symbol, loss, target):
    posicoes_abertas_var = posicoes_abertas(symbol)
    percent = posicoes_abertas_var[5]
    pnl = posicoes_abertas_var[6]

    if percent:
        if percent < loss:
            encerra_posicao(symbol)
            print(f"Posição encerrada por stop loss {pnl}")
            # telegram
            # time.sleep(3000)
        elif percent >= target:
            encerra_posicao(symbol)
            print(f"Posição encerrada por take profit {pnl}")
            # telegram


def max_tamanho_exposto_atingido(symbol, max_tamanho_exposto):
    posicoes_abertas_var = posicoes_abertas(symbol)
    tamanho_exposto = posicoes_abertas_var[1]
    if (
        isinstance(tamanho_exposto, float)
        and float(tamanho_exposto) >= max_tamanho_exposto
    ):
        return True

    return False


def ultima_ordem_esta_aberta(symbol):
    open_orders = binance.fetch_orders(symbol)[-1]["status"]

    last_order = open_orders[-1] if len(open_orders) > 0 else None
    if not last_order:
        return False

    return True if open_orders == "open" else False

"""Brazilian Receita Federal monthly report (IN 1888 / 1888/2019).

Required columns (per RFB guidelines for crypto operations):
  - Data da operação
  - Tipo (compra | venda)
  - Ativo (BTC)
  - Quantidade
  - Valor unitário (BRL)
  - Valor total (BRL)
  - Taxas
  - Exchange (Binance / Mercado Bitcoin)

For Binance trades in USDT, we convert to BRL at the trade timestamp using
the quote-day BRL/USDT close (BCB PTAX or exchange ticker fallback).

Operations under R$35.000 / month total are exempt from filing but recorded
here for audit trail.

TODO:
  - implement BRL conversion for USDT-quoted trades
  - integrate with BCB PTAX endpoint for daily exchange rates
  - emit CSV to reports/ir/YYYY-MM.csv
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from decimal import Decimal


@dataclass(slots=True)
class IRRow:
    operation_date: date
    operation_type: str       # "compra" | "venda"
    asset: str                # "BTC"
    quantity: Decimal
    unit_price_brl: Decimal
    total_brl: Decimal
    fees_brl: Decimal
    exchange: str

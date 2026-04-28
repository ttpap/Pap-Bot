"""High-level engine that wires indicators → confluence → risk → AI filter → exchange.

Pseudocode for one tick:
    candles = await exchange.get_ohlcv(timeframe, limit=200)
    df = pandas.DataFrame(candles)
    confluence = strategy.evaluate(df.close)
    if abs(confluence.score) < settings.min_confluence_score:
        return
    ai = await ai_filter.current_decision()
    if ai.verdict == VETO:
        return
    bankroll = await ledger.get_bankroll(exchange.name)
    allowed, reason = risk.can_open(today=today, bankroll=bankroll)
    if not allowed:
        log(reason)
        return
    atr_value = risk.atr(df).iloc[-1]
    side = "buy" if confluence.signal is BUY else "sell"
    plan = risk.plan_trade(
        side=side,
        bankroll=bankroll,
        entry_price=df.close.iloc[-1],
        atr_value=atr_value,
        ai_size_multiplier=ai.size_multiplier,
        quantity_step=exchange.quantity_step,
    )
    if plan is None:
        return
    order = await exchange.place_market_order(side, plan.quantity)
    await exchange.place_oco_order(opposite(side), plan.quantity, plan.take_profit, plan.stop_loss)
    await ledger.record_trade(...)
"""

from __future__ import annotations

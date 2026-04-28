"""CLI entrypoint."""

from __future__ import annotations

from datetime import date, datetime

import typer
from rich.console import Console

from btc_bot.config import Mode, settings

app = typer.Typer(no_args_is_help=True, help="BTC trading bot — Binance + Mercado Bitcoin")
console = Console()


@app.command()
def run(
    mode: Mode | None = typer.Option(
        None,
        help="Override BTC_BOT_MODE from .env (backtest | paper | live)",
    ),
) -> None:
    """Start the bot in the configured mode."""
    effective = mode or settings.mode
    console.print(f"[bold cyan]Starting bot in mode:[/bold cyan] {effective.value}")
    console.print(f"Enabled exchanges: {settings.enabled_exchanges}")
    console.print("[yellow]TODO: wire up engine and start scheduler[/yellow]")


@app.command()
def backtest(
    start: datetime = typer.Option(..., help="Start date (YYYY-MM-DD)"),
    end: datetime = typer.Option(..., help="End date (YYYY-MM-DD)"),
    exchange: str = typer.Option("binance", help="binance | mb"),
) -> None:
    """Run a backtest over the given date range."""
    console.print(f"Backtest {exchange}: {start.date()} → {end.date()}")
    console.print("[yellow]TODO: implement backtest engine[/yellow]")


@app.command()
def report(
    month: str = typer.Option(..., help="YYYY-MM"),
) -> None:
    """Generate Receita Federal IR-ready CSV for the given month."""
    console.print(f"IR report for {month}")
    console.print("[yellow]TODO: implement IR exporter[/yellow]")


@app.command()
def gate() -> None:
    """Check whether the live trading gate has been satisfied."""
    console.print("[yellow]TODO: read latest backtest result and validate gate[/yellow]")


if __name__ == "__main__":
    app()

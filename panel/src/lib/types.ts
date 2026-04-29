// ----- Bot status -----

export type Mode = "backtest" | "paper" | "live";
export type ExchangeId = "binance" | "mb";

export interface ExchangeStatus {
  id: ExchangeId;
  enabled: boolean;
  symbol: string;            // BTC/USDT or BTC/BRL
  quote: string;             // USDT or BRL
  bankroll: number;          // current bankroll in quote currency
  bankroll_pct_change_24h: number;
  open_position: Position | null;
  last_signal: ConfluenceSnapshot | null;
  ops_today: number;
  realized_pnl_today: number;
  paused: boolean;
  paused_reason?: string;
}

export interface BotStatus {
  mode: Mode;
  uptime_seconds: number;
  exchanges: ExchangeStatus[];
  ai: AIStatus;
  gate: GateStatus;
  ts: string;                // ISO timestamp
}

// ----- Confluence -----

export type Signal = "BUY" | "SELL" | "NEUTRAL";

export interface IndicatorReading {
  name: string;
  value: number | null;
  signal: -1 | 0 | 1;
  weight: number;
}

export interface ConfluenceSnapshot {
  ts: string;
  score: number;             // signed
  score_buy: number;
  score_sell: number;
  signal: Signal;
  components: IndicatorReading[];
}

// ----- Positions / trades -----

export interface Position {
  id: string;
  exchange: ExchangeId;
  symbol: string;
  side: "buy" | "sell";
  quantity: number;
  entry_price: number;
  current_price: number;
  stop_loss: number;
  take_profit: number;
  unrealized_pnl: number;
  unrealized_pnl_pct: number;
  opened_at: string;
}

export interface Trade {
  id: string;
  exchange: ExchangeId;
  symbol: string;
  side: "buy" | "sell";
  mode: Mode;
  quantity: number;
  entry_price: number;
  exit_price: number | null;
  stop_loss: number;
  take_profit: number;
  pnl: number | null;
  fees: number;
  confluence_score: number;
  ai_verdict: AIVerdict | null;
  opened_at: string;
  closed_at: string | null;
}

// ----- AI -----

export type AIVerdict = "veto" | "reduce" | "neutral" | "boost";

export interface AIStatus {
  verdict: AIVerdict;
  size_multiplier: number;
  reasoning: string;
  flagged_items: string[];
  refreshed_at: string;
}

// ----- Credentials -----

export type ProviderId = "binance" | "mb" | "anthropic";

export interface CredentialStatus {
  provider: ProviderId;
  configured: boolean;
  last_updated: string | null;
  last_tested: string | null;
  test_result: "ok" | "auth_failed" | "ip_not_whitelisted" | "other_error" | null;
  test_message: string | null;
  // Permission flags reported by the exchange (read after a successful test)
  withdraw_enabled: boolean | null;
  trade_enabled: boolean | null;
}

export interface CredentialsState {
  binance: CredentialStatus;
  mb: CredentialStatus;
  anthropic: CredentialStatus;
}

// ----- Backtest gate -----

export interface BacktestStats {
  n_trades: number;
  win_rate: number;          // 0..1
  sharpe: number;
  max_drawdown: number;      // 0..1
  profit_factor: number;
  total_return: number;
  final_equity: number;
}

export interface GateStatus {
  passed: boolean;
  exchange: ExchangeId;
  ran_at: string | null;
  start: string | null;
  end: string | null;
  initial_bankroll: number | null;
  stats: BacktestStats | null;
  thresholds: {
    min_sharpe: number;
    max_drawdown: number;
    min_win_rate: number;
  };
}

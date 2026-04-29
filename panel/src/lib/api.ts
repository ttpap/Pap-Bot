// API client for the bot's FastAPI service.
//
// All requests go through the Next.js server-side proxy at /api/bot
// to avoid CORS, client-bundle env var issues, and key exposure.
// The proxy injects the X-API-Key server-side.

import type {
  BotStatus,
  Trade,
  Mode,
  ExchangeId,
  GateStatus,
  AIStatus,
  CredentialsState,
  ProviderId,
} from "./types";

/** Proxy a request through the Next.js /api/bot route handler. */
async function botFetch<T>(
  botPath: string,
  init?: RequestInit
): Promise<T | null> {
  // botPath e.g. "credentials" → /api/bot?path=credentials
  const url = `/api/bot?path=${encodeURIComponent(botPath)}`;
  try {
    const res = await fetch(url, {
      ...init,
      headers: { "Content-Type": "application/json", ...(init?.headers ?? {}) },
      cache: "no-store",
    });
    if (!res.ok) return null;
    return (await res.json()) as T;
  } catch {
    return null;
  }
}

/** Same but throws on error so callers can show a message. */
async function botMutate<T>(botPath: string, init: RequestInit): Promise<T> {
  const url = `/api/bot?path=${encodeURIComponent(botPath)}`;
  const res = await fetch(url, {
    ...init,
    headers: { "Content-Type": "application/json", ...(init?.headers ?? {}) },
  });
  return (await res.json()) as T;
}

// ----- mock data ---------------------------------------------------------

const MOCK_STATUS: BotStatus = {
  mode: "backtest",
  uptime_seconds: 3 * 3600 + 17 * 60,
  ts: new Date().toISOString(),
  ai: {
    verdict: "neutral",
    size_multiplier: 1,
    reasoning:
      "No high-impact regulatory or exchange-outage news in the last 15m. CryptoPanic momentum slightly positive but below boost threshold.",
    flagged_items: [],
    refreshed_at: new Date(Date.now() - 7 * 60_000).toISOString(),
  },
  gate: {
    passed: false,
    exchange: "binance",
    ran_at: null,
    start: null,
    end: null,
    initial_bankroll: null,
    stats: null,
    thresholds: {
      min_sharpe: 1.0,
      max_drawdown: 0.2,
      min_win_rate: 0.45,
    },
  },
  exchanges: [
    {
      id: "binance",
      enabled: true,
      symbol: "BTC/USDT",
      quote: "USDT",
      bankroll: 50.0,
      bankroll_pct_change_24h: 0,
      open_position: null,
      ops_today: 0,
      realized_pnl_today: 0,
      paused: false,
      last_signal: {
        ts: new Date(Date.now() - 12 * 60_000).toISOString(),
        score: -3,
        score_buy: 2,
        score_sell: 3,
        signal: "SELL",
        components: [
          { name: "MA",  value: 1, signal: 1, weight: 2 },
          { name: "RSI", value: 73.4, signal: -1, weight: 2 },
          { name: "BB",  value: 0, signal: 0, weight: 1 },
          { name: "RCI", value: 88.2, signal: -1, weight: 1 },
        ],
      },
    },
    {
      id: "mb",
      enabled: true,
      symbol: "BTC/BRL",
      quote: "BRL",
      bankroll: 250.0,
      bankroll_pct_change_24h: 0,
      open_position: null,
      ops_today: 0,
      realized_pnl_today: 0,
      paused: false,
      last_signal: {
        ts: new Date(Date.now() - 12 * 60_000).toISOString(),
        score: 0,
        score_buy: 2,
        score_sell: 2,
        signal: "NEUTRAL",
        components: [
          { name: "MA",  value: 1, signal: 1, weight: 2 },
          { name: "RSI", value: 56.2, signal: 0, weight: 2 },
          { name: "BB",  value: 0, signal: 0, weight: 1 },
          { name: "RCI", value: 22.7, signal: 0, weight: 1 },
        ],
      },
    },
  ],
};

const MOCK_TRADES: Trade[] = [];

// ----- public API (all via server-side proxy at /api/bot) ----------------

export async function getStatus(): Promise<BotStatus> {
  return (await botFetch<BotStatus>("status")) ?? MOCK_STATUS;
}

export async function getTrades(limit = 50): Promise<Trade[]> {
  return (await botFetch<Trade[]>(`trades?limit=${limit}`)) ?? MOCK_TRADES;
}

export async function getGate(): Promise<GateStatus> {
  return (await botFetch<GateStatus>("gate")) ?? MOCK_STATUS.gate;
}

export async function getAI(): Promise<AIStatus> {
  return (await botFetch<AIStatus>("ai")) ?? MOCK_STATUS.ai;
}

export async function setMode(mode: Mode): Promise<void> {
  await botMutate("mode", {
    method: "POST",
    body: JSON.stringify({ mode }),
  });
}

export async function toggleExchange(
  id: ExchangeId,
  enabled: boolean
): Promise<void> {
  await botMutate(`exchanges/${id}/toggle`, {
    method: "POST",
    body: JSON.stringify({ enabled }),
  });
}

// ----- credentials -------------------------------------------------------

export async function getCredentials(): Promise<CredentialsState> {
  return (
    (await botFetch<CredentialsState>("credentials")) ?? {
      binance:   { provider: "binance",   configured: false, last_updated: null, last_tested: null, test_result: null, test_message: null, withdraw_enabled: null, trade_enabled: null },
      mb:        { provider: "mb",        configured: false, last_updated: null, last_tested: null, test_result: null, test_message: null, withdraw_enabled: null, trade_enabled: null },
      anthropic: { provider: "anthropic", configured: false, last_updated: null, last_tested: null, test_result: null, test_message: null, withdraw_enabled: null, trade_enabled: null },
    }
  );
}

export interface SaveCredentialPayload {
  provider: ProviderId;
  api_key: string;
  api_secret?: string;
}

export interface SaveCredentialResponse {
  ok: boolean;
  message: string;
  status?: CredentialsState[ProviderId];
}

export async function saveCredential(
  payload: SaveCredentialPayload
): Promise<SaveCredentialResponse> {
  return botMutate<SaveCredentialResponse>("credentials", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export async function testCredential(
  provider: ProviderId
): Promise<SaveCredentialResponse> {
  return botMutate<SaveCredentialResponse>(`credentials/${provider}/test`, {
    method: "POST",
    body: JSON.stringify({}),
  });
}

export async function deleteCredential(
  provider: ProviderId
): Promise<SaveCredentialResponse> {
  return botMutate<SaveCredentialResponse>(`credentials/${provider}`, {
    method: "DELETE",
  });
}

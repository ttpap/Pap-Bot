// API client for the bot's FastAPI service.
// Set NEXT_PUBLIC_BOT_API_URL to override (default http://localhost:8000).
//
// While the bot endpoints are still being built, this client falls back to a
// deterministic mock so the UI is fully navigable end-to-end.

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

const BASE = process.env.NEXT_PUBLIC_BOT_API_URL ?? "http://localhost:8000";
const USE_MOCK = process.env.NEXT_PUBLIC_USE_MOCK !== "false";
const API_KEY = process.env.NEXT_PUBLIC_BOT_API_KEY ?? "";

function authHeaders(extra: Record<string, string> = {}): Record<string, string> {
  return { accept: "application/json", "X-API-Key": API_KEY, ...extra };
}

async function tryFetch<T>(path: string): Promise<T | null> {
  if (USE_MOCK) return null;
  try {
    const res = await fetch(`${BASE}${path}`, {
      headers: authHeaders(),
      cache: "no-store",
    });
    if (!res.ok) return null;
    return (await res.json()) as T;
  } catch {
    return null;
  }
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

const MOCK_TRADES: Trade[] = [
  // empty until first run
];

// ----- public API --------------------------------------------------------

export async function getStatus(): Promise<BotStatus> {
  return (await tryFetch<BotStatus>("/api/status")) ?? MOCK_STATUS;
}

export async function getTrades(limit = 50): Promise<Trade[]> {
  return (
    (await tryFetch<Trade[]>(`/api/trades?limit=${limit}`)) ?? MOCK_TRADES
  );
}

export async function getGate(): Promise<GateStatus> {
  return (
    (await tryFetch<GateStatus>("/api/gate")) ?? MOCK_STATUS.gate
  );
}

export async function getAI(): Promise<AIStatus> {
  return (await tryFetch<AIStatus>("/api/ai")) ?? MOCK_STATUS.ai;
}

export async function setMode(mode: Mode): Promise<void> {
  if (USE_MOCK) return;
  await fetch(`${BASE}/api/mode`, {
    method: "POST",
    headers: authHeaders({ "content-type": "application/json" }),
    body: JSON.stringify({ mode }),
  });
}

export async function toggleExchange(
  id: ExchangeId,
  enabled: boolean
): Promise<void> {
  if (USE_MOCK) return;
  await fetch(`${BASE}/api/exchanges/${id}/toggle`, {
    method: "POST",
    headers: authHeaders({ "content-type": "application/json" }),
    body: JSON.stringify({ enabled }),
  });
}

// ----- credentials -----

const MOCK_CREDENTIALS: CredentialsState = {
  binance: {
    provider: "binance",
    configured: false,
    last_updated: null,
    last_tested: null,
    test_result: null,
    test_message: null,
    withdraw_enabled: null,
    trade_enabled: null,
  },
  mb: {
    provider: "mb",
    configured: false,
    last_updated: null,
    last_tested: null,
    test_result: null,
    test_message: null,
    withdraw_enabled: null,
    trade_enabled: null,
  },
  anthropic: {
    provider: "anthropic",
    configured: false,
    last_updated: null,
    last_tested: null,
    test_result: null,
    test_message: null,
    withdraw_enabled: null,
    trade_enabled: null,
  },
};

export async function getCredentials(): Promise<CredentialsState> {
  return (
    (await tryFetch<CredentialsState>("/api/credentials")) ?? MOCK_CREDENTIALS
  );
}

export interface SaveCredentialPayload {
  provider: ProviderId;
  api_key: string;
  api_secret?: string; // anthropic only uses api_key
}

export interface SaveCredentialResponse {
  ok: boolean;
  message: string;
  status?: CredentialsState[ProviderId];
}

export async function saveCredential(
  payload: SaveCredentialPayload
): Promise<SaveCredentialResponse> {
  if (USE_MOCK) {
    // Simulate latency + a basic length check
    await new Promise((r) => setTimeout(r, 600));
    if (payload.api_key.length < 16) {
      return { ok: false, message: "API key looks too short — please double-check." };
    }
    return {
      ok: true,
      message:
        "Saved (mock). When the bot backend is online this will encrypt and persist the key on the server.",
    };
  }
  const res = await fetch(`${BASE}/api/credentials`, {
    method: "POST",
    headers: authHeaders({ "content-type": "application/json" }),
    body: JSON.stringify(payload),
  });
  return (await res.json()) as SaveCredentialResponse;
}

export async function testCredential(
  provider: ProviderId
): Promise<SaveCredentialResponse> {
  if (USE_MOCK) {
    await new Promise((r) => setTimeout(r, 800));
    return { ok: false, message: "Bot backend offline (mock mode)." };
  }
  const res = await fetch(`${BASE}/api/credentials/${provider}/test`, {
    method: "POST",
    headers: authHeaders(),
  });
  return (await res.json()) as SaveCredentialResponse;
}

export async function deleteCredential(
  provider: ProviderId
): Promise<SaveCredentialResponse> {
  if (USE_MOCK) {
    await new Promise((r) => setTimeout(r, 300));
    return { ok: true, message: "Cleared (mock)." };
  }
  const res = await fetch(`${BASE}/api/credentials/${provider}`, {
    method: "DELETE",
    headers: authHeaders(),
  });
  return (await res.json()) as SaveCredentialResponse;
}

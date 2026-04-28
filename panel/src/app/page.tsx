import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Separator } from "@/components/ui/separator";
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import { PageHeader } from "@/components/page-header";
import { ModePill } from "@/components/mode-pill";
import { SignalPill } from "@/components/signal-pill";
import { getStatus } from "@/lib/api";
import { fmtDuration, fmtMoney, fmtPct, fmtRelative } from "@/lib/format";
import { AlertTriangle, Sparkles } from "lucide-react";

export default async function OverviewPage() {
  const status = await getStatus();

  const totalOpsToday = status.exchanges.reduce(
    (s, e) => s + e.ops_today,
    0
  );

  return (
    <>
      <PageHeader
        title="Overview"
        description="Live status of the trading bot, per-exchange bankroll, and most recent confluence signal."
        actions={<ModePill mode={status.mode} />}
      />

      <div className="px-6 sm:px-8 py-6 space-y-6">
        {!status.gate.passed && (
          <Alert variant="default" className="border-amber-700/40 bg-amber-950/30">
            <AlertTriangle className="h-4 w-4 text-amber-500" />
            <AlertTitle>Live mode locked</AlertTitle>
            <AlertDescription>
              The backtest gate has not been satisfied yet. Live trading is
              disabled until a backtest run produces Sharpe &gt;{" "}
              {status.gate.thresholds.min_sharpe}, max drawdown &lt;{" "}
              {fmtPct(status.gate.thresholds.max_drawdown)}, win rate &gt;{" "}
              {fmtPct(status.gate.thresholds.min_win_rate)}.
            </AlertDescription>
          </Alert>
        )}

        {/* Top-level stats */}
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
          <StatCard label="Mode" value={status.mode} mono />
          <StatCard
            label="Uptime"
            value={fmtDuration(status.uptime_seconds)}
            mono
          />
          <StatCard label="Ops today" value={String(totalOpsToday)} mono />
        </div>

        {/* Exchanges */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
          {status.exchanges.map((ex) => (
            <Card key={ex.id} className="overflow-hidden">
              <CardHeader>
                <div className="flex items-center justify-between">
                  <div>
                    <CardTitle className="flex items-center gap-2">
                      {ex.id === "binance" ? "Binance" : "Mercado Bitcoin"}
                      {!ex.enabled && (
                        <Badge variant="secondary" className="text-xs">
                          disabled
                        </Badge>
                      )}
                      {ex.paused && (
                        <Badge
                          variant="destructive"
                          className="text-xs"
                          title={ex.paused_reason}
                        >
                          paused
                        </Badge>
                      )}
                    </CardTitle>
                    <CardDescription className="font-mono">
                      {ex.symbol}
                    </CardDescription>
                  </div>
                  {ex.last_signal && (
                    <SignalPill
                      signal={ex.last_signal.signal}
                      score={ex.last_signal.score}
                    />
                  )}
                </div>
              </CardHeader>
              <CardContent>
                <div className="grid grid-cols-2 gap-4">
                  <Field
                    label="Bankroll"
                    value={fmtMoney(ex.bankroll, ex.quote)}
                  />
                  <Field
                    label="P&L today"
                    value={fmtMoney(ex.realized_pnl_today, ex.quote)}
                    tone={
                      ex.realized_pnl_today > 0
                        ? "pos"
                        : ex.realized_pnl_today < 0
                          ? "neg"
                          : undefined
                    }
                  />
                  <Field
                    label="Ops today"
                    value={`${ex.ops_today} / 5`}
                  />
                  <Field
                    label="Open position"
                    value={
                      ex.open_position
                        ? `${ex.open_position.side.toUpperCase()} ${ex.open_position.quantity} BTC`
                        : "—"
                    }
                  />
                </div>
                <Separator className="my-4" />
                <div className="space-y-2">
                  <div className="text-xs text-muted-foreground uppercase tracking-wide">
                    Last indicator readings
                  </div>
                  {ex.last_signal ? (
                    <div className="grid grid-cols-4 gap-2">
                      {ex.last_signal.components.map((c) => (
                        <IndicatorChip
                          key={c.name}
                          name={c.name}
                          signal={c.signal}
                          weight={c.weight}
                        />
                      ))}
                    </div>
                  ) : (
                    <div className="text-sm text-muted-foreground">
                      Awaiting first candle close…
                    </div>
                  )}
                  {ex.last_signal && (
                    <div className="text-[11px] text-muted-foreground pt-2">
                      Refreshed {fmtRelative(ex.last_signal.ts)}
                    </div>
                  )}
                </div>
              </CardContent>
            </Card>
          ))}
        </div>

        {/* AI filter */}
        <Card>
          <CardHeader>
            <div className="flex items-center justify-between">
              <CardTitle className="flex items-center gap-2">
                <Sparkles className="h-4 w-4 text-violet-400" />
                AI news / sentiment filter
              </CardTitle>
              <Badge
                variant="outline"
                className="font-mono tracking-wider uppercase"
              >
                {status.ai.verdict}
              </Badge>
            </div>
            <CardDescription className="text-xs">
              Refreshed {fmtRelative(status.ai.refreshed_at)} · size multiplier{" "}
              <span className="font-mono">{status.ai.size_multiplier.toFixed(2)}x</span>
            </CardDescription>
          </CardHeader>
          <CardContent>
            <p className="text-sm text-muted-foreground leading-relaxed">
              {status.ai.reasoning}
            </p>
            {status.ai.flagged_items.length > 0 && (
              <ul className="mt-3 list-disc list-inside text-sm text-foreground/80 space-y-0.5">
                {status.ai.flagged_items.map((item, i) => (
                  <li key={i}>{item}</li>
                ))}
              </ul>
            )}
          </CardContent>
        </Card>
      </div>
    </>
  );
}

function StatCard({
  label,
  value,
  mono,
}: {
  label: string;
  value: string;
  mono?: boolean;
}) {
  return (
    <Card>
      <CardContent className="py-5">
        <div className="text-xs uppercase tracking-wider text-muted-foreground">
          {label}
        </div>
        <div className={`text-2xl mt-1 ${mono ? "font-mono" : ""}`}>
          {value}
        </div>
      </CardContent>
    </Card>
  );
}

function Field({
  label,
  value,
  tone,
}: {
  label: string;
  value: string;
  tone?: "pos" | "neg";
}) {
  return (
    <div>
      <div className="text-xs uppercase tracking-wider text-muted-foreground">
        {label}
      </div>
      <div
        className={`text-lg font-mono mt-0.5 ${
          tone === "pos"
            ? "text-emerald-400"
            : tone === "neg"
              ? "text-rose-400"
              : ""
        }`}
      >
        {value}
      </div>
    </div>
  );
}

function IndicatorChip({
  name,
  signal,
  weight,
}: {
  name: string;
  signal: -1 | 0 | 1;
  weight: number;
}) {
  const color =
    signal === 1
      ? "border-emerald-700/40 bg-emerald-600/15 text-emerald-400"
      : signal === -1
        ? "border-rose-700/40 bg-rose-600/15 text-rose-400"
        : "border-zinc-700/60 bg-zinc-800/40 text-zinc-400";
  return (
    <div className={`rounded-md border px-2 py-1.5 ${color}`}>
      <div className="text-[10px] uppercase tracking-wider opacity-70">
        {name} · w{weight}
      </div>
      <div className="font-mono text-xs">
        {signal === 1 ? "BUY" : signal === -1 ? "SELL" : "—"}
      </div>
    </div>
  );
}

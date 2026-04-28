import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Separator } from "@/components/ui/separator";
import { PageHeader } from "@/components/page-header";
import { getGate } from "@/lib/api";
import { fmtMoney, fmtNumber, fmtPct, fmtDateTime } from "@/lib/format";
import { CheckCircle2, XCircle } from "lucide-react";

export default async function BacktestPage() {
  const gate = await getGate();

  return (
    <>
      <PageHeader
        title="Backtest gate"
        description="Live trading is locked until a backtest produces metrics that beat the configured thresholds."
      />
      <div className="px-6 sm:px-8 py-6 space-y-6">
        <Card>
          <CardHeader>
            <div className="flex items-center justify-between">
              <div>
                <CardTitle className="flex items-center gap-2">
                  Gate status
                  {gate.passed ? (
                    <Badge className="bg-emerald-600 text-white">PASSED</Badge>
                  ) : (
                    <Badge variant="destructive">LOCKED</Badge>
                  )}
                </CardTitle>
                <CardDescription>
                  Exchange: {gate.exchange === "binance" ? "Binance" : "Mercado Bitcoin"}
                  {gate.ran_at && ` · last ran ${fmtDateTime(gate.ran_at)}`}
                </CardDescription>
              </div>
            </div>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
              <Threshold
                label="Sharpe"
                actual={gate.stats?.sharpe}
                target={gate.thresholds.min_sharpe}
                cmp=">"
                fmt={(v) => fmtNumber(v, 2)}
              />
              <Threshold
                label="Max drawdown"
                actual={gate.stats?.max_drawdown}
                target={gate.thresholds.max_drawdown}
                cmp="<"
                fmt={fmtPct}
              />
              <Threshold
                label="Win rate"
                actual={gate.stats?.win_rate}
                target={gate.thresholds.min_win_rate}
                cmp=">"
                fmt={fmtPct}
              />
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Last backtest run</CardTitle>
            <CardDescription>
              {gate.stats
                ? `${fmtDateTime(gate.start ?? "")} → ${fmtDateTime(gate.end ?? "")}`
                : "No backtest has been run yet."}
            </CardDescription>
          </CardHeader>
          <CardContent>
            {gate.stats ? (
              <>
                <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
                  <Field label="Trades" value={String(gate.stats.n_trades)} />
                  <Field label="Win rate" value={fmtPct(gate.stats.win_rate)} />
                  <Field label="Profit factor" value={fmtNumber(gate.stats.profit_factor, 2)} />
                  <Field
                    label="Total return"
                    value={fmtPct(gate.stats.total_return)}
                    tone={gate.stats.total_return >= 0 ? "pos" : "neg"}
                  />
                </div>
                <Separator className="my-4" />
                <div className="grid grid-cols-2 sm:grid-cols-3 gap-4">
                  <Field
                    label="Initial bankroll"
                    value={
                      gate.initial_bankroll != null
                        ? fmtMoney(gate.initial_bankroll, "USDT")
                        : "—"
                    }
                  />
                  <Field label="Final equity" value={fmtMoney(gate.stats.final_equity, "USDT")} />
                  <Field
                    label="Max drawdown"
                    value={fmtPct(gate.stats.max_drawdown)}
                    tone="neg"
                  />
                </div>
              </>
            ) : (
              <div className="rounded-md border border-dashed border-border py-12 text-center text-sm text-muted-foreground">
                <p>Run a backtest from the CLI to populate this view:</p>
                <pre className="mt-3 inline-block rounded-md bg-muted/40 px-3 py-2 text-xs font-mono">
                  btc-bot backtest --start 2024-01-01 --end 2024-06-30 --exchange binance
                </pre>
              </div>
            )}
          </CardContent>
        </Card>
      </div>
    </>
  );
}

function Threshold({
  label,
  actual,
  target,
  cmp,
  fmt,
}: {
  label: string;
  actual: number | undefined;
  target: number;
  cmp: ">" | "<";
  fmt: (v: number) => string;
}) {
  const pass =
    actual != null && (cmp === ">" ? actual > target : actual < target);
  return (
    <div className="rounded-md border border-border bg-card/50 p-4">
      <div className="text-xs text-muted-foreground uppercase tracking-wider">
        {label}
      </div>
      <div className="mt-1 flex items-baseline gap-2">
        <div className="text-2xl font-mono">
          {actual != null ? fmt(actual) : "—"}
        </div>
        <div className="text-xs text-muted-foreground font-mono">
          {cmp} {fmt(target)}
        </div>
      </div>
      <div className="mt-2 flex items-center gap-1.5 text-xs">
        {actual == null ? (
          <span className="text-muted-foreground">no run</span>
        ) : pass ? (
          <>
            <CheckCircle2 className="h-3.5 w-3.5 text-emerald-500" />
            <span className="text-emerald-400">pass</span>
          </>
        ) : (
          <>
            <XCircle className="h-3.5 w-3.5 text-rose-500" />
            <span className="text-rose-400">fail</span>
          </>
        )}
      </div>
    </div>
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
      <div className="text-xs text-muted-foreground uppercase tracking-wider">
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

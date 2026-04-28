import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { Badge } from "@/components/ui/badge";
import { PageHeader } from "@/components/page-header";
import { ModePill } from "@/components/mode-pill";
import { getTrades } from "@/lib/api";
import { fmtDateTime, fmtMoney, fmtNumber } from "@/lib/format";

export default async function TradesPage() {
  const trades = await getTrades(100);

  return (
    <>
      <PageHeader
        title="Trade history"
        description="Every fill recorded by the bot. Bankrolls are tracked separately per exchange — there is no fund mixing."
      />
      <div className="px-6 sm:px-8 py-6">
        <Card>
          <CardHeader>
            <CardTitle>Recent trades</CardTitle>
            <CardDescription>
              Showing the last {trades.length} {trades.length === 1 ? "trade" : "trades"}.
              Trades from backtest, paper and live modes are tagged independently.
            </CardDescription>
          </CardHeader>
          <CardContent>
            {trades.length === 0 ? (
              <div className="rounded-md border border-dashed border-border py-16 text-center text-sm text-muted-foreground">
                <p>No trades yet.</p>
                <p className="mt-1 text-xs">
                  Run a backtest from the <span className="font-mono">Backtest</span> tab to populate this table.
                </p>
              </div>
            ) : (
              <div className="overflow-x-auto">
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead>Opened</TableHead>
                      <TableHead>Exchange</TableHead>
                      <TableHead>Mode</TableHead>
                      <TableHead>Side</TableHead>
                      <TableHead className="text-right">Qty</TableHead>
                      <TableHead className="text-right">Entry</TableHead>
                      <TableHead className="text-right">Exit</TableHead>
                      <TableHead className="text-right">PnL</TableHead>
                      <TableHead className="text-right">Score</TableHead>
                      <TableHead>AI</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {trades.map((t) => (
                      <TableRow key={t.id}>
                        <TableCell className="font-mono text-xs">
                          {fmtDateTime(t.opened_at)}
                        </TableCell>
                        <TableCell>{t.exchange === "binance" ? "Binance" : "MB"}</TableCell>
                        <TableCell>
                          <ModePill mode={t.mode} />
                        </TableCell>
                        <TableCell>
                          <Badge
                            variant="outline"
                            className={
                              t.side === "buy"
                                ? "border-emerald-700/40 bg-emerald-600/10 text-emerald-400"
                                : "border-rose-700/40 bg-rose-600/10 text-rose-400"
                            }
                          >
                            {t.side.toUpperCase()}
                          </Badge>
                        </TableCell>
                        <TableCell className="text-right font-mono text-xs">
                          {fmtNumber(t.quantity, 5)}
                        </TableCell>
                        <TableCell className="text-right font-mono text-xs">
                          {fmtMoney(t.entry_price, t.exchange === "binance" ? "USDT" : "BRL")}
                        </TableCell>
                        <TableCell className="text-right font-mono text-xs">
                          {t.exit_price
                            ? fmtMoney(t.exit_price, t.exchange === "binance" ? "USDT" : "BRL")
                            : "—"}
                        </TableCell>
                        <TableCell
                          className={`text-right font-mono text-xs ${
                            t.pnl == null
                              ? ""
                              : t.pnl >= 0
                                ? "text-emerald-400"
                                : "text-rose-400"
                          }`}
                        >
                          {t.pnl != null
                            ? fmtMoney(t.pnl, t.exchange === "binance" ? "USDT" : "BRL")
                            : "open"}
                        </TableCell>
                        <TableCell className="text-right font-mono text-xs">
                          {t.confluence_score > 0
                            ? `+${t.confluence_score}`
                            : t.confluence_score}
                        </TableCell>
                        <TableCell>
                          {t.ai_verdict ? (
                            <Badge
                              variant="outline"
                              className="text-[10px] uppercase tracking-wider"
                            >
                              {t.ai_verdict}
                            </Badge>
                          ) : (
                            <span className="text-xs text-muted-foreground">—</span>
                          )}
                        </TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              </div>
            )}
          </CardContent>
        </Card>
      </div>
    </>
  );
}

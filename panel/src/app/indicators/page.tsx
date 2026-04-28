import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Separator } from "@/components/ui/separator";
import { PageHeader } from "@/components/page-header";
import { SignalPill } from "@/components/signal-pill";
import { getStatus } from "@/lib/api";
import { fmtNumber, fmtRelative } from "@/lib/format";

export default async function IndicatorsPage() {
  const status = await getStatus();

  return (
    <>
      <PageHeader
        title="Indicators"
        description="Latest readings per exchange. Confluence threshold is a weighted score ≥ 4 (MA=2, RSI=2, BB=1, RCI=1)."
      />
      <div className="px-6 sm:px-8 py-6 space-y-6">
        {status.exchanges.map((ex) => (
          <Card key={ex.id}>
            <CardHeader>
              <div className="flex items-center justify-between">
                <div>
                  <CardTitle className="flex items-center gap-2">
                    {ex.id === "binance" ? "Binance" : "Mercado Bitcoin"}
                    <span className="text-xs text-muted-foreground font-mono">
                      {ex.symbol}
                    </span>
                  </CardTitle>
                  <CardDescription>
                    {ex.last_signal
                      ? `Refreshed ${fmtRelative(ex.last_signal.ts)}`
                      : "Awaiting first candle close"}
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
              {ex.last_signal ? (
                <>
                  <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
                    {ex.last_signal.components.map((c) => (
                      <div
                        key={c.name}
                        className="rounded-md border border-border bg-card/50 p-4"
                      >
                        <div className="text-xs text-muted-foreground uppercase tracking-wider">
                          {c.name}{" "}
                          <span className="opacity-60">w{c.weight}</span>
                        </div>
                        <div className="mt-1 text-2xl font-mono">
                          {c.value != null ? fmtNumber(c.value, 2) : "—"}
                        </div>
                        <div className="mt-2">
                          <SignalPill
                            signal={
                              c.signal === 1
                                ? "BUY"
                                : c.signal === -1
                                  ? "SELL"
                                  : "NEUTRAL"
                            }
                          />
                        </div>
                      </div>
                    ))}
                  </div>
                  <Separator className="my-4" />
                  <div className="grid grid-cols-3 gap-4 text-sm">
                    <div>
                      <div className="text-xs text-muted-foreground uppercase tracking-wider">
                        Score (signed)
                      </div>
                      <div className="text-xl font-mono mt-1">
                        {ex.last_signal.score > 0
                          ? `+${ex.last_signal.score}`
                          : ex.last_signal.score}
                      </div>
                    </div>
                    <div>
                      <div className="text-xs text-muted-foreground uppercase tracking-wider">
                        Buy votes
                      </div>
                      <div className="text-xl font-mono mt-1 text-emerald-400">
                        {ex.last_signal.score_buy}
                      </div>
                    </div>
                    <div>
                      <div className="text-xs text-muted-foreground uppercase tracking-wider">
                        Sell votes
                      </div>
                      <div className="text-xl font-mono mt-1 text-rose-400">
                        {ex.last_signal.score_sell}
                      </div>
                    </div>
                  </div>
                </>
              ) : (
                <div className="text-sm text-muted-foreground">
                  Indicators will populate after the first complete 15m candle.
                </div>
              )}
            </CardContent>
          </Card>
        ))}
      </div>
    </>
  );
}

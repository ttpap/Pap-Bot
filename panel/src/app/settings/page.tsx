"use client";

import { useState } from "react";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Switch } from "@/components/ui/switch";
import { Label } from "@/components/ui/label";
import { Separator } from "@/components/ui/separator";
import { Button } from "@/components/ui/button";
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import { PageHeader } from "@/components/page-header";
import { Lock } from "lucide-react";
import type { Mode } from "@/lib/types";

export default function SettingsPage() {
  const [mode, setMode] = useState<Mode>("backtest");
  const [binanceEnabled, setBinanceEnabled] = useState(true);
  const [mbEnabled, setMBEnabled] = useState(true);

  return (
    <>
      <PageHeader
        title="Settings"
        description="Configure mode and per-exchange enable/disable. Live mode requires a passing backtest gate."
      />
      <div className="px-6 sm:px-8 py-6 space-y-6 max-w-3xl">
        <Card>
          <CardHeader>
            <CardTitle>Mode</CardTitle>
            <CardDescription>
              Switch between backtest, paper trading, and live execution.
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="flex items-center gap-3">
              <Select
                value={mode}
                onValueChange={(v) => setMode(v as Mode)}
              >
                <SelectTrigger className="w-48">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="backtest">Backtest</SelectItem>
                  <SelectItem value="paper">Paper trading</SelectItem>
                  <SelectItem value="live" disabled>
                    Live (gate locked)
                  </SelectItem>
                </SelectContent>
              </Select>
              <Button>Apply</Button>
            </div>
            <Alert className="mt-4 border-amber-700/40 bg-amber-950/30">
              <Lock className="h-4 w-4 text-amber-500" />
              <AlertTitle>Live mode locked</AlertTitle>
              <AlertDescription>
                Live execution becomes selectable once the backtest gate passes
                (Sharpe &gt; 1, max DD &lt; 20%, win rate &gt; 45%).
              </AlertDescription>
            </Alert>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Exchanges</CardTitle>
            <CardDescription>
              Each exchange runs an isolated bankroll — there is no cross-exchange transfer.
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="flex items-center justify-between">
              <div>
                <Label htmlFor="binance" className="text-sm">
                  Binance
                </Label>
                <p className="text-xs text-muted-foreground mt-0.5 font-mono">
                  BTC/USDT spot
                </p>
              </div>
              <Switch
                id="binance"
                checked={binanceEnabled}
                onCheckedChange={setBinanceEnabled}
              />
            </div>
            <Separator />
            <div className="flex items-center justify-between">
              <div>
                <Label htmlFor="mb" className="text-sm">
                  Mercado Bitcoin
                </Label>
                <p className="text-xs text-muted-foreground mt-0.5 font-mono">
                  BTC/BRL spot
                </p>
              </div>
              <Switch
                id="mb"
                checked={mbEnabled}
                onCheckedChange={setMBEnabled}
              />
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Risk parameters</CardTitle>
            <CardDescription>
              Active values from the bot config. Edit via <span className="font-mono">.env</span>; UI editing arrives once the API is wired.
            </CardDescription>
          </CardHeader>
          <CardContent>
            <dl className="grid grid-cols-2 gap-y-3 text-sm">
              <ParamRow label="Position size" value="50% bankroll / order" />
              <ParamRow label="Stop loss" value="1.5 × ATR" />
              <ParamRow label="Take profit" value="3 × ATR" />
              <ParamRow label="Daily loss cap" value="3% → 24h pause" />
              <ParamRow label="Max ops / day" value="5" />
              <ParamRow label="Confluence threshold" value="weighted ≥ 4" />
              <ParamRow label="Timeframe" value="15m" />
              <ParamRow label="AI refresh interval" value="15 min" />
            </dl>
          </CardContent>
        </Card>
      </div>
    </>
  );
}

function ParamRow({ label, value }: { label: string; value: string }) {
  return (
    <>
      <dt className="text-muted-foreground">{label}</dt>
      <dd className="font-mono text-right">{value}</dd>
    </>
  );
}

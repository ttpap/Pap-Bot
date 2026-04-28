import { Badge } from "@/components/ui/badge";
import type { Mode } from "@/lib/types";

const STYLES: Record<Mode, string> = {
  backtest: "bg-zinc-700 text-zinc-100 hover:bg-zinc-700",
  paper: "bg-blue-600 text-white hover:bg-blue-600",
  live: "bg-emerald-600 text-white hover:bg-emerald-600",
};

const LABELS: Record<Mode, string> = {
  backtest: "BACKTEST",
  paper: "PAPER",
  live: "LIVE",
};

export function ModePill({ mode }: { mode: Mode }) {
  return (
    <Badge className={STYLES[mode] + " font-mono tracking-wider"}>
      {LABELS[mode]}
    </Badge>
  );
}

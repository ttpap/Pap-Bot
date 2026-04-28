import { Badge } from "@/components/ui/badge";
import type { Signal } from "@/lib/types";

export function SignalPill({ signal, score }: { signal: Signal; score?: number }) {
  const map: Record<Signal, string> = {
    BUY: "bg-emerald-600/20 text-emerald-400 border-emerald-700/40",
    SELL: "bg-rose-600/20 text-rose-400 border-rose-700/40",
    NEUTRAL: "bg-zinc-700/30 text-zinc-300 border-zinc-700",
  };
  return (
    <Badge variant="outline" className={`${map[signal]} font-mono tracking-wider`}>
      {signal}
      {typeof score === "number" && (
        <span className="ml-1.5 opacity-70">
          {score > 0 ? `+${score}` : score}
        </span>
      )}
    </Badge>
  );
}

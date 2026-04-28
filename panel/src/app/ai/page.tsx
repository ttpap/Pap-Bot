import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { PageHeader } from "@/components/page-header";
import { getAI } from "@/lib/api";
import { fmtRelative } from "@/lib/format";

const VERDICT_STYLES: Record<string, string> = {
  veto: "bg-rose-600 text-white",
  reduce: "bg-amber-600 text-white",
  neutral: "bg-zinc-700 text-zinc-100",
  boost: "bg-emerald-600 text-white",
};

const VERDICT_DESC: Record<string, string> = {
  veto: "Hard block on new entries until news posture improves.",
  reduce: "Halve trade size on next entry.",
  neutral: "No filter applied — risk manager controls sizing.",
  boost: "Multiply size by 1.2× on next entry (still capped at 50% bankroll).",
};

export default async function AIPage() {
  const ai = await getAI();

  return (
    <>
      <PageHeader
        title="AI news / sentiment filter"
        description="Claude Sonnet reviews macro, regulatory, exchange, and on-chain news every 15 minutes. The verdict gates or amplifies entries from the confluence engine."
      />
      <div className="px-6 sm:px-8 py-6 space-y-6">
        <Card>
          <CardHeader>
            <div className="flex items-center justify-between">
              <div>
                <CardTitle>Current verdict</CardTitle>
                <CardDescription>
                  Refreshed {fmtRelative(ai.refreshed_at)} · multiplier{" "}
                  <span className="font-mono">{ai.size_multiplier.toFixed(2)}x</span>
                </CardDescription>
              </div>
              <Badge
                className={`${VERDICT_STYLES[ai.verdict]} font-mono uppercase tracking-wider px-3 py-1`}
              >
                {ai.verdict}
              </Badge>
            </div>
          </CardHeader>
          <CardContent className="space-y-4">
            <p className="text-sm text-muted-foreground italic">
              {VERDICT_DESC[ai.verdict]}
            </p>
            <div>
              <div className="text-xs uppercase tracking-wider text-muted-foreground mb-2">
                Reasoning
              </div>
              <p className="text-sm leading-relaxed">{ai.reasoning}</p>
            </div>
            {ai.flagged_items.length > 0 && (
              <div>
                <div className="text-xs uppercase tracking-wider text-muted-foreground mb-2">
                  Flagged items
                </div>
                <ul className="text-sm space-y-1">
                  {ai.flagged_items.map((item, i) => (
                    <li key={i} className="flex gap-2">
                      <span className="text-muted-foreground">·</span>
                      <span>{item}</span>
                    </li>
                  ))}
                </ul>
              </div>
            )}
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Verdict semantics</CardTitle>
            <CardDescription>
              How each verdict affects trade sizing relative to the 50% bankroll cap.
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3">
              <SemanticCard verdict="veto" multiplier="0.0×" />
              <SemanticCard verdict="reduce" multiplier="0.5×" />
              <SemanticCard verdict="neutral" multiplier="1.0×" />
              <SemanticCard verdict="boost" multiplier="1.2×" />
            </div>
          </CardContent>
        </Card>
      </div>
    </>
  );
}

function SemanticCard({
  verdict,
  multiplier,
}: {
  verdict: string;
  multiplier: string;
}) {
  return (
    <div className="rounded-md border border-border bg-card/50 p-4">
      <Badge
        className={`${VERDICT_STYLES[verdict]} font-mono uppercase tracking-wider`}
      >
        {verdict}
      </Badge>
      <div className="mt-3 text-xl font-mono">{multiplier}</div>
      <p className="mt-2 text-xs text-muted-foreground leading-relaxed">
        {VERDICT_DESC[verdict]}
      </p>
    </div>
  );
}

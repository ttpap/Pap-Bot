"use client";

import { useState } from "react";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Separator } from "@/components/ui/separator";
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
  AlertDialogTrigger,
} from "@/components/ui/alert-dialog";
import {
  Eye,
  EyeOff,
  CheckCircle2,
  XCircle,
  AlertTriangle,
  RotateCw,
  Trash2,
} from "lucide-react";
import { fmtRelative } from "@/lib/format";
import {
  saveCredential,
  testCredential,
  deleteCredential,
} from "@/lib/api";
import type { CredentialStatus, ProviderId } from "@/lib/types";

interface Props {
  provider: ProviderId;
  title: string;
  subtitle: string;
  needsSecret: boolean;            // anthropic only needs api_key
  apiKeyHelp?: string;
  whitelistIp?: string;
  initialStatus: CredentialStatus;
}

export function CredentialCard({
  provider,
  title,
  subtitle,
  needsSecret,
  apiKeyHelp,
  whitelistIp,
  initialStatus,
}: Props) {
  const [status, setStatus] = useState(initialStatus);
  const [apiKey, setApiKey] = useState("");
  const [apiSecret, setApiSecret] = useState("");
  const [showKey, setShowKey] = useState(false);
  const [showSecret, setShowSecret] = useState(false);
  const [busy, setBusy] = useState(false);
  const [feedback, setFeedback] = useState<{ ok: boolean; msg: string } | null>(
    null
  );

  async function handleSave(e: React.FormEvent) {
    e.preventDefault();
    setBusy(true);
    setFeedback(null);
    try {
      const result = await saveCredential({
        provider,
        api_key: apiKey,
        api_secret: needsSecret ? apiSecret : undefined,
      });
      setFeedback({ ok: result.ok, msg: result.message });
      if (result.ok && result.status) {
        setStatus(result.status);
        setApiKey("");
        setApiSecret("");
      }
    } finally {
      setBusy(false);
    }
  }

  async function handleTest() {
    setBusy(true);
    setFeedback(null);
    try {
      const result = await testCredential(provider);
      setFeedback({ ok: result.ok, msg: result.message });
      if (result.status) setStatus(result.status);
    } finally {
      setBusy(false);
    }
  }

  async function handleDelete() {
    setBusy(true);
    setFeedback(null);
    try {
      const result = await deleteCredential(provider);
      setFeedback({ ok: result.ok, msg: result.message });
      if (result.ok) {
        setStatus({
          ...status,
          configured: false,
          last_updated: null,
          last_tested: null,
          test_result: null,
          test_message: null,
          withdraw_enabled: null,
          trade_enabled: null,
        });
      }
    } finally {
      setBusy(false);
    }
  }

  return (
    <Card>
      <CardHeader>
        <div className="flex items-start justify-between gap-3">
          <div>
            <CardTitle className="flex items-center gap-2">
              {title}
              {status.configured ? (
                <Badge className="bg-emerald-600 text-white text-[10px]">
                  CONFIGURED
                </Badge>
              ) : (
                <Badge variant="outline" className="text-[10px]">
                  NOT SET
                </Badge>
              )}
            </CardTitle>
            <CardDescription>{subtitle}</CardDescription>
          </div>
          {status.configured && (
            <Button
              variant="ghost"
              size="sm"
              onClick={handleTest}
              disabled={busy}
              title="Test connection"
            >
              <RotateCw className="h-4 w-4" />
            </Button>
          )}
        </div>
      </CardHeader>

      <CardContent className="space-y-4">
        {/* Per-exchange security checklist */}
        {provider !== "anthropic" && (
          <div className="rounded-md border border-amber-700/40 bg-amber-950/20 px-3 py-2 text-xs space-y-1">
            <div className="flex items-center gap-1.5 text-amber-400 font-medium">
              <AlertTriangle className="h-3.5 w-3.5" />
              Before generating this key, set the restrictions below
            </div>
            <ul className="text-amber-300/80 space-y-0.5 ml-5 list-disc">
              <li>
                Withdraw permission: <span className="font-mono">DISABLED</span>
              </li>
              <li>
                Spot trading: <span className="font-mono">ENABLED</span>
              </li>
              {whitelistIp && (
                <li>
                  IP whitelist: include{" "}
                  <span className="font-mono">{whitelistIp}</span>
                </li>
              )}
            </ul>
          </div>
        )}

        <form onSubmit={handleSave} className="space-y-3" autoComplete="off">
          <div>
            <div className="flex items-center justify-between">
              <Label htmlFor={`${provider}-key`} className="text-xs">
                API Key
              </Label>
              <button
                type="button"
                className="text-xs text-muted-foreground hover:text-foreground flex items-center gap-1"
                onClick={() => setShowKey((v) => !v)}
              >
                {showKey ? <EyeOff className="h-3 w-3" /> : <Eye className="h-3 w-3" />}
                {showKey ? "hide" : "show"}
              </button>
            </div>
            <Input
              id={`${provider}-key`}
              type={showKey ? "text" : "password"}
              value={apiKey}
              onChange={(e) => setApiKey(e.target.value)}
              placeholder={status.configured ? "•".repeat(24) + " (masked)" : "Paste your API key"}
              className="font-mono mt-1.5"
              autoComplete="off"
              spellCheck={false}
            />
            {apiKeyHelp && (
              <p className="text-[11px] text-muted-foreground mt-1">{apiKeyHelp}</p>
            )}
          </div>

          {needsSecret && (
            <div>
              <div className="flex items-center justify-between">
                <Label htmlFor={`${provider}-secret`} className="text-xs">
                  API Secret
                </Label>
                <button
                  type="button"
                  className="text-xs text-muted-foreground hover:text-foreground flex items-center gap-1"
                  onClick={() => setShowSecret((v) => !v)}
                >
                  {showSecret ? <EyeOff className="h-3 w-3" /> : <Eye className="h-3 w-3" />}
                  {showSecret ? "hide" : "show"}
                </button>
              </div>
              <Input
                id={`${provider}-secret`}
                type={showSecret ? "text" : "password"}
                value={apiSecret}
                onChange={(e) => setApiSecret(e.target.value)}
                placeholder={status.configured ? "•".repeat(40) + " (masked)" : "Paste your API secret"}
                className="font-mono mt-1.5"
                autoComplete="off"
                spellCheck={false}
              />
            </div>
          )}

          <div className="flex items-center gap-2 pt-1">
            <Button type="submit" disabled={busy || !apiKey || (needsSecret && !apiSecret)}>
              {busy ? "Saving…" : status.configured ? "Replace" : "Save"}
            </Button>
            {status.configured && (
              <AlertDialog>
                <AlertDialogTrigger
                  render={
                    <Button type="button" variant="ghost" size="sm" disabled={busy}>
                      <Trash2 className="h-4 w-4 mr-1.5" />
                      Remove
                    </Button>
                  }
                />
                <AlertDialogContent>
                  <AlertDialogHeader>
                    <AlertDialogTitle>Remove {title} credentials?</AlertDialogTitle>
                    <AlertDialogDescription>
                      The encrypted key will be deleted from the bot. The bot
                      will stop trading on this provider until a new key is
                      saved.
                    </AlertDialogDescription>
                  </AlertDialogHeader>
                  <AlertDialogFooter>
                    <AlertDialogCancel>Cancel</AlertDialogCancel>
                    <AlertDialogAction onClick={handleDelete}>
                      Remove
                    </AlertDialogAction>
                  </AlertDialogFooter>
                </AlertDialogContent>
              </AlertDialog>
            )}
          </div>

          {feedback && (
            <div
              className={`text-xs rounded-md px-3 py-2 border ${
                feedback.ok
                  ? "border-emerald-700/40 bg-emerald-950/30 text-emerald-300"
                  : "border-rose-700/40 bg-rose-950/30 text-rose-300"
              }`}
            >
              {feedback.msg}
            </div>
          )}
        </form>

        {status.configured && (
          <>
            <Separator />
            <div className="grid grid-cols-2 gap-3 text-xs">
              <div>
                <div className="text-muted-foreground uppercase tracking-wider">
                  Last updated
                </div>
                <div className="font-mono mt-0.5">
                  {status.last_updated ? fmtRelative(status.last_updated) : "—"}
                </div>
              </div>
              <div>
                <div className="text-muted-foreground uppercase tracking-wider">
                  Last test
                </div>
                <div className="font-mono mt-0.5 flex items-center gap-1">
                  {status.test_result === "ok" && (
                    <>
                      <CheckCircle2 className="h-3 w-3 text-emerald-500" />
                      <span className="text-emerald-400">ok</span>
                    </>
                  )}
                  {status.test_result &&
                    status.test_result !== "ok" && (
                      <>
                        <XCircle className="h-3 w-3 text-rose-500" />
                        <span className="text-rose-400">
                          {status.test_result}
                        </span>
                      </>
                    )}
                  {!status.test_result && "—"}
                </div>
              </div>
              {provider !== "anthropic" && (
                <>
                  <div>
                    <div className="text-muted-foreground uppercase tracking-wider">
                      Trade
                    </div>
                    <div className="font-mono mt-0.5">
                      {status.trade_enabled === true && (
                        <span className="text-emerald-400">enabled</span>
                      )}
                      {status.trade_enabled === false && (
                        <span className="text-rose-400">disabled</span>
                      )}
                      {status.trade_enabled == null && "—"}
                    </div>
                  </div>
                  <div>
                    <div className="text-muted-foreground uppercase tracking-wider">
                      Withdraw
                    </div>
                    <div className="font-mono mt-0.5">
                      {status.withdraw_enabled === false && (
                        <span className="text-emerald-400">disabled ✓</span>
                      )}
                      {status.withdraw_enabled === true && (
                        <span className="text-rose-400 font-bold">
                          ENABLED — disable in exchange
                        </span>
                      )}
                      {status.withdraw_enabled == null && "—"}
                    </div>
                  </div>
                </>
              )}
            </div>
          </>
        )}
      </CardContent>
    </Card>
  );
}

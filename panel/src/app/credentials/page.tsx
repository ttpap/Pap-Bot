import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import { ShieldCheck } from "lucide-react";
import { PageHeader } from "@/components/page-header";
import { CredentialCard } from "@/components/credential-card";
import { getCredentials } from "@/lib/api";

export default async function CredentialsPage() {
  const creds = await getCredentials();

  // VM IP that needs to go in the exchange whitelist
  const VM_IP = process.env.NEXT_PUBLIC_BOT_HOST_IP ?? "137.131.148.111";

  return (
    <>
      <PageHeader
        title="API credentials"
        description="Configure exchange and AI provider keys. Keys are encrypted at rest on the bot, never displayed back, and never sent to your browser after they are saved."
      />

      <div className="px-6 sm:px-8 py-6 space-y-6 max-w-3xl">
        <Alert className="border-emerald-700/40 bg-emerald-950/20">
          <ShieldCheck className="h-4 w-4 text-emerald-500" />
          <AlertTitle>How keys are handled</AlertTitle>
          <AlertDescription>
            <ul className="text-xs space-y-1 mt-1">
              <li>
                · Submitted over HTTPS to the bot, encrypted with Fernet, written
                to <span className="font-mono">/secrets</span> on the VM.
              </li>
              <li>
                · Never re-displayed in plaintext after saving — only status,
                last update, and last test result.
              </li>
              <li>
                · Browser never persists keys (no localStorage, no cookies).
              </li>
              <li>
                · The bot tests each key with a read-only call (e.g. account
                permissions) and refuses to start trading if{" "}
                <span className="font-mono">withdraw_enabled = true</span>.
              </li>
            </ul>
          </AlertDescription>
        </Alert>

        <CredentialCard
          provider="binance"
          title="Binance"
          subtitle="BTC/USDT spot — generate at api.binance.com → API Management"
          needsSecret
          whitelistIp={VM_IP}
          apiKeyHelp="Format: 64 alphanumeric characters."
          initialStatus={creds.binance}
        />

        <CredentialCard
          provider="mb"
          title="Mercado Bitcoin"
          subtitle="BTC/BRL spot — generate at mercadobitcoin.com.br → My account → API"
          needsSecret
          whitelistIp={VM_IP}
          apiKeyHelp="Format: UUID-style key paired with secret."
          initialStatus={creds.mb}
        />

        <CredentialCard
          provider="anthropic"
          title="Anthropic"
          subtitle="Claude Sonnet 4.6 — used for the AI news / sentiment filter"
          needsSecret={false}
          apiKeyHelp="Starts with sk-ant-. Generate at console.anthropic.com/settings/keys."
          initialStatus={creds.anthropic}
        />
      </div>
    </>
  );
}

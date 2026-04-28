"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import {
  Activity,
  BarChart3,
  History,
  KeyRound,
  Settings,
  LineChart,
  Sparkles,
} from "lucide-react";
import { cn } from "@/lib/utils";
import { Separator } from "@/components/ui/separator";

const items = [
  { href: "/", label: "Overview", icon: Activity },
  { href: "/trades", label: "Trades", icon: History },
  { href: "/indicators", label: "Indicators", icon: LineChart },
  { href: "/backtest", label: "Backtest", icon: BarChart3 },
  { href: "/ai", label: "AI Filter", icon: Sparkles },
  { href: "/credentials", label: "Credentials", icon: KeyRound },
  { href: "/settings", label: "Settings", icon: Settings },
];

export function Nav() {
  const pathname = usePathname();
  return (
    <aside className="hidden md:flex w-60 shrink-0 flex-col border-r border-border bg-sidebar">
      <div className="px-6 py-5">
        <Link href="/" className="flex items-center gap-2">
          <div className="h-7 w-7 rounded-md bg-orange-500 flex items-center justify-center text-black font-bold text-sm">
            ₿
          </div>
          <div className="leading-tight">
            <div className="font-semibold text-sm">btc-bot</div>
            <div className="text-[10px] text-muted-foreground uppercase tracking-wider">
              Confluence engine
            </div>
          </div>
        </Link>
      </div>
      <Separator />
      <nav className="flex-1 px-3 py-4 space-y-1">
        {items.map(({ href, label, icon: Icon }) => {
          const active =
            href === "/" ? pathname === "/" : pathname.startsWith(href);
          return (
            <Link
              key={href}
              href={href}
              className={cn(
                "flex items-center gap-3 rounded-md px-3 py-2 text-sm transition-colors",
                active
                  ? "bg-sidebar-accent text-sidebar-accent-foreground font-medium"
                  : "text-muted-foreground hover:bg-sidebar-accent/40 hover:text-foreground"
              )}
            >
              <Icon className="h-4 w-4" />
              {label}
            </Link>
          );
        })}
      </nav>
      <Separator />
      <div className="px-4 py-3 text-[11px] text-muted-foreground">
        <div className="flex items-center gap-2">
          <div className="h-1.5 w-1.5 rounded-full bg-emerald-500 animate-pulse" />
          <span>API connected</span>
        </div>
      </div>
    </aside>
  );
}

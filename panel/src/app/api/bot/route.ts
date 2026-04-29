/**
 * Server-side proxy to the bot FastAPI backend.
 *
 * All requests to /api/bot/* are forwarded to the bot API with the correct
 * X-API-Key header injected server-side. This avoids:
 *   - CORS issues (browser → bot)
 *   - NEXT_PUBLIC_ env var baking problems in static bundles
 *   - Exposing the API key in the client bundle
 *
 * Usage from client:
 *   fetch('/api/bot/credentials')          → GET  BOT_API_URL/api/credentials
 *   fetch('/api/bot/credentials', {POST})  → POST BOT_API_URL/api/credentials
 */

import { NextRequest, NextResponse } from "next/server";

const BOT_URL = process.env.BOT_API_URL ?? process.env.NEXT_PUBLIC_BOT_API_URL ?? "http://localhost:8000";
const BOT_KEY = process.env.BOT_API_KEY ?? process.env.NEXT_PUBLIC_BOT_API_KEY ?? "";

async function proxy(req: NextRequest, path: string): Promise<NextResponse> {
  const upstreamUrl = `${BOT_URL}/api/${path}`;

  const headers: Record<string, string> = {
    "X-API-Key": BOT_KEY,
    "Content-Type": "application/json",
    Accept: "application/json",
  };

  let body: string | undefined;
  if (req.method !== "GET" && req.method !== "HEAD") {
    try {
      body = await req.text();
    } catch {
      body = undefined;
    }
  }

  try {
    const upstream = await fetch(upstreamUrl, {
      method: req.method,
      headers,
      body,
      cache: "no-store",
    });

    const data = await upstream.json();
    return NextResponse.json(data, { status: upstream.status });
  } catch (err) {
    return NextResponse.json(
      { ok: false, message: `Bot unreachable: ${err instanceof Error ? err.message : String(err)}` },
      { status: 502 }
    );
  }
}

export async function GET(req: NextRequest) {
  const path = req.nextUrl.searchParams.get("path") ?? "credentials";
  return proxy(req, path);
}

export async function POST(req: NextRequest) {
  const path = req.nextUrl.searchParams.get("path") ?? "credentials";
  return proxy(req, path);
}

export async function DELETE(req: NextRequest) {
  const path = req.nextUrl.searchParams.get("path") ?? "credentials";
  return proxy(req, path);
}

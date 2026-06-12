"use client";

import { useEffect, useState } from "react";

const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

type ServiceStatus = { status: string; details?: string | null };
type Health = { status: string; services: Record<string, ServiceStatus> };

const TONE: Record<string, string> = {
  OK: "text-emerald-400 border-emerald-500/40 bg-emerald-500/10",
  DEGRADED: "text-amber-400 border-amber-500/40 bg-amber-500/10",
  PARTIAL: "text-sky-400 border-sky-500/40 bg-sky-500/10",
  ERROR: "text-rose-400 border-rose-500/40 bg-rose-500/10",
  NOT_INITIALIZED: "text-neutral-400 border-neutral-500/40 bg-neutral-500/10",
};

function Badge({ value }: { value: string }) {
  const tone = TONE[value] ?? TONE.NOT_INITIALIZED;
  return <span className={`rounded-md border px-2 py-0.5 font-mono text-xs ${tone}`}>{value}</span>;
}

export default function Home() {
  const [health, setHealth] = useState<Health | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    async function load() {
      try {
        const res = await fetch(`${API_URL}/api/health/check`, { cache: "no-store" });
        if (!res.ok) {
          setHealth(null);
          setError(`backend returned ${res.status}`);
          return;
        }
        setHealth((await res.json()) as Health);
        setError(null);
      } catch (e) {
        setHealth(null);
        setError(e instanceof Error ? e.message : "request failed");
      }
    }
    load();
    const id = setInterval(load, 5000);
    return () => clearInterval(id);
  }, []);

  return (
    <main className="mx-auto flex min-h-screen max-w-xl flex-col justify-center gap-6 px-6">
      <header>
        <h1 className="text-2xl font-semibold">Vibe Starter</h1>
        <p className="text-sm text-neutral-400">
          Minimal placeholder app. The point of this repo is the{" "}
          <code className="font-mono text-neutral-200">.vibe/</code> configuration.
        </p>
      </header>

      <section className="rounded-xl border border-neutral-800 bg-neutral-900/50 p-5">
        <div className="mb-4 flex items-center justify-between">
          <span className="text-sm text-neutral-400">Backend health</span>
          <Badge value={health?.status ?? "NOT_INITIALIZED"} />
        </div>

        {error && (
          <p className="font-mono text-xs text-rose-400">
            {error} — is the backend running on {API_URL}?
          </p>
        )}

        {health?.services && (
          <ul className="flex flex-col gap-2">
            {Object.entries(health.services).map(([name, svc]) => (
              <li key={name} className="flex items-center justify-between text-sm">
                <span className="font-mono text-neutral-300">{name}</span>
                <Badge value={svc.status} />
              </li>
            ))}
          </ul>
        )}
      </section>

      <p className="text-center font-mono text-xs text-neutral-600">
        GET {API_URL}/api/health/check · refreshes every 5s
      </p>
    </main>
  );
}

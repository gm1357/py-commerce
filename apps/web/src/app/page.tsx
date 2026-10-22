import { healthGetHealth } from "api-client";
import { connection } from "next/server";
import { Suspense } from "react";

export default function Home() {
  return (
    <main className="mx-auto flex w-full max-w-xl flex-1 flex-col gap-8 px-4 py-24">
      <div>
        <h1 className="text-3xl font-semibold tracking-tight">py-commerce</h1>
        <p className="mt-2 text-zinc-600 dark:text-zinc-400">
          Next.js frontend talking to the FastAPI backend through the generated api-client.
        </p>
      </div>
      <Suspense fallback={<StatusList api="checking" database="checking" />}>
        <SystemStatus />
      </Suspense>
    </main>
  );
}

async function SystemStatus() {
  await connection(); // health must be checked per request, never prerendered
  const status = await fetchStatus();
  return <StatusList {...status} />;
}

async function fetchStatus(): Promise<{ api: string; database: string }> {
  try {
    const { data, error } = await healthGetHealth();
    if (error || !data) return { api: "error", database: "unknown" };
    return { api: data.status, database: data.database };
  } catch {
    // fetch throws when the API isn't running at all
    return { api: "unreachable", database: "unknown" };
  }
}

function StatusList({ api, database }: { api: string; database: string }) {
  return (
    <dl className="grid grid-cols-[max-content_1fr] gap-x-6 gap-y-2 rounded-lg border border-zinc-200 p-4 font-mono text-sm dark:border-zinc-800">
      <dt className="text-zinc-500">API</dt>
      <dd className={statusColor(api)}>{api}</dd>
      <dt className="text-zinc-500">Database</dt>
      <dd className={statusColor(database)}>{database}</dd>
    </dl>
  );
}

function statusColor(value: string) {
  if (value === "ok") return "text-green-600 dark:text-green-400";
  if (value === "checking") return "text-zinc-500";
  return "text-red-600 dark:text-red-400";
}

"use client"; // Error boundaries must be Client Components

import { useEffect } from "react";

export default function Error({ error, retry }: { error: unknown; retry: () => void }) {
  useEffect(() => {
    console.error(error);
  }, [error]);

  return (
    <div className="flex flex-col items-start gap-4">
      <h1 className="text-3xl font-semibold tracking-tight">Something went wrong</h1>
      <p className="text-zinc-600 dark:text-zinc-400">
        The request couldn&apos;t be completed. Is the API running?
      </p>
      <button onClick={() => retry()} className="underline">
        Try again
      </button>
    </div>
  );
}

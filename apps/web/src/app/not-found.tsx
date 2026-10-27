import Link from "next/link";

export default function NotFound() {
  return (
    <div className="flex flex-col items-start gap-4">
      <h1 className="text-3xl font-semibold tracking-tight">Not found</h1>
      <p className="text-zinc-600 dark:text-zinc-400">
        This page doesn&apos;t exist, or what it showed has been deleted.
      </p>
      <Link href="/" className="underline">
        Back to all products
      </Link>
    </div>
  );
}

import Link from "next/link";

const linkClass = "rounded-md border border-zinc-300 px-3 py-1.5 hover:bg-zinc-100 dark:border-zinc-700 dark:hover:bg-zinc-900";
const disabledClass = "rounded-md border border-zinc-200 px-3 py-1.5 text-zinc-400 dark:border-zinc-800 dark:text-zinc-600";

/** Previous/next links that set `?page=` on `basePath` (the product list by default). */
export function Pagination({
  page,
  pages,
  basePath = "/",
}: {
  page: number;
  pages: number;
  basePath?: string;
}) {
  return (
    <nav aria-label="Pagination" className="flex items-center justify-between text-sm">
      {page > 1 ? (
        <Link href={`${basePath}?page=${page - 1}`} className={linkClass}>
          ← Previous
        </Link>
      ) : (
        <span className={disabledClass}>← Previous</span>
      )}
      <span className="text-zinc-600 dark:text-zinc-400">
        Page {page} of {pages}
      </span>
      {page < pages ? (
        <Link href={`${basePath}?page=${page + 1}`} className={linkClass}>
          Next →
        </Link>
      ) : (
        <span className={disabledClass}>Next →</span>
      )}
    </nav>
  );
}

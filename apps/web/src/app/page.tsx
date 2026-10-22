import { productsListProducts } from "api-client";
import Link from "next/link";
import { Suspense } from "react";

import { Pagination } from "@/components/pagination";
import { getCurrentUser } from "@/lib/auth";
import { formatCents } from "@/lib/money";

export default function Home(props: PageProps<"/">) {
  return (
    <div className="flex flex-col gap-8">
      <div className="flex items-center justify-between gap-4">
        <h1 className="text-3xl font-semibold tracking-tight">Products</h1>
        <Suspense>
          <NewProductLink />
        </Suspense>
      </div>
      <Suspense fallback={<ProductGridSkeleton />}>
        <ProductList searchParams={props.searchParams} />
      </Suspense>
    </div>
  );
}

async function NewProductLink() {
  const user = await getCurrentUser();
  if (user?.role !== "admin") return null;

  return (
    <Link
      href="/products/new"
      className="rounded-md bg-zinc-900 px-4 py-2 font-medium text-white dark:bg-zinc-100 dark:text-zinc-900"
    >
      New product
    </Link>
  );
}

async function ProductList({ searchParams }: { searchParams: PageProps<"/">["searchParams"] }) {
  const pageParam = Number((await searchParams).page);
  const page = Number.isInteger(pageParam) && pageParam >= 1 ? pageParam : 1;

  const { data } = await productsListProducts({ query: { page } });
  if (!data) return <Notice>Couldn&apos;t load products. Is the API running?</Notice>;
  if (data.total === 0) return <Notice>No products yet. Create the first one!</Notice>;
  if (data.items.length === 0) {
    return (
      <Notice>
        Page {page} doesn&apos;t exist.{" "}
        <Link href="/" className="underline">
          Go to page 1
        </Link>
      </Notice>
    );
  }

  return (
    <div className="flex flex-col gap-6">
      <ul className="grid gap-4 sm:grid-cols-2">
        {data.items.map((product) => (
          <li key={product.id}>
            <Link
              href={`/products/${product.id}`}
              className="flex h-full flex-col gap-2 rounded-lg border border-zinc-200 p-4 transition-colors hover:border-zinc-400 dark:border-zinc-800 dark:hover:border-zinc-600"
            >
              <div className="flex items-baseline justify-between gap-3">
                <h2 className="font-medium">{product.name}</h2>
                <span className="font-mono text-sm">{formatCents(product.price)}</span>
              </div>
              {product.description && (
                <p className="line-clamp-2 text-sm text-zinc-600 dark:text-zinc-400">
                  {product.description}
                </p>
              )}
            </Link>
          </li>
        ))}
      </ul>
      <Pagination page={data.page} pages={data.pages} />
    </div>
  );
}

function Notice({ children }: { children: React.ReactNode }) {
  return (
    <p className="rounded-lg border border-dashed border-zinc-300 p-8 text-center text-zinc-600 dark:border-zinc-700 dark:text-zinc-400">
      {children}
    </p>
  );
}

function ProductGridSkeleton() {
  return (
    <ul className="grid gap-4 sm:grid-cols-2" aria-busy="true" aria-label="Loading products">
      {Array.from({ length: 10 }, (_, i) => (
        <li key={i} className="h-24 animate-pulse rounded-lg bg-zinc-100 dark:bg-zinc-900" />
      ))}
    </ul>
  );
}

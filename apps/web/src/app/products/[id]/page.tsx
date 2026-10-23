import Link from "next/link";
import { Suspense } from "react";

import { DeleteProductButton } from "@/components/delete-product-button";
import { getCurrentUser } from "@/lib/auth";
import { formatDate } from "@/lib/dates";
import { formatCents } from "@/lib/money";
import { getProductOrNotFound } from "@/lib/products";

import { deleteProductAction } from "../actions";

export default function ProductPage(props: PageProps<"/products/[id]">) {
  return (
    <div className="flex flex-col gap-6">
      <Link href="/" className="text-sm text-zinc-600 hover:underline dark:text-zinc-400">
        ← All products
      </Link>
      <Suspense fallback={<div className="h-48 animate-pulse rounded-lg bg-zinc-100 dark:bg-zinc-900" />}>
        <ProductDetails params={props.params} />
      </Suspense>
    </div>
  );
}

async function ProductDetails({ params }: { params: PageProps<"/products/[id]">["params"] }) {
  const { id } = await params;
  const [product, user] = await Promise.all([getProductOrNotFound(id), getCurrentUser()]);

  return (
    <article className="flex flex-col gap-6">
      <div className="flex flex-col gap-2">
        <h1 className="text-3xl font-semibold tracking-tight">{product.name}</h1>
        <p className="font-mono text-xl">{formatCents(product.price)}</p>
      </div>
      <p className="whitespace-pre-line text-zinc-700 dark:text-zinc-300">
        {product.description || <span className="italic text-zinc-500">No description.</span>}
      </p>
      <dl className="grid grid-cols-[max-content_1fr] gap-x-6 gap-y-1 text-sm text-zinc-500">
        <dt>Created</dt>
        <dd>{formatDate(product.created_at)}</dd>
        <dt>Updated</dt>
        <dd>{formatDate(product.updated_at)}</dd>
      </dl>
      {user?.role === "admin" && (
        <div className="flex items-center gap-3">
          <Link
            href={`/products/${product.id}/edit`}
            className="rounded-md bg-zinc-900 px-4 py-2 font-medium text-white dark:bg-zinc-100 dark:text-zinc-900"
          >
            Edit
          </Link>
          <DeleteProductButton action={deleteProductAction.bind(null, product.id)} />
        </div>
      )}
    </article>
  );
}

import { cartGetCart } from "api-client";
import Link from "next/link";
import { Suspense } from "react";

import { ActionButton } from "@/components/action-button";
import { Notice } from "@/components/notice";
import { QuantityForm } from "@/components/quantity-form";
import { getSessionToken, requireUser } from "@/lib/auth";
import { formatCents } from "@/lib/money";

import { checkoutAction, removeCartItemAction, updateCartItemAction } from "./actions";

export default function CartPage() {
  return (
    <div className="flex flex-col gap-8">
      <h1 className="text-3xl font-semibold tracking-tight">Your cart</h1>
      <Suspense fallback={<div className="h-48 animate-pulse rounded-lg bg-zinc-100 dark:bg-zinc-900" />}>
        <Cart />
      </Suspense>
    </div>
  );
}

async function Cart() {
  await requireUser();
  const { data } = await cartGetCart({ auth: await getSessionToken() });
  if (!data) throw new Error("Failed to load the cart");

  if (data.items.length === 0) {
    return (
      <Notice>
        Your cart is empty.{" "}
        <Link href="/" className="underline">
          Browse products
        </Link>
      </Notice>
    );
  }

  return (
    <div className="flex flex-col gap-6">
      <ul className="divide-y divide-zinc-200 border-y border-zinc-200 dark:divide-zinc-800 dark:border-zinc-800">
        {data.items.map(({ product, quantity, subtotal }) => (
          <li key={product.id} className="flex flex-wrap items-start justify-between gap-4 py-4">
            <div className="flex flex-col gap-1">
              <Link href={`/products/${product.id}`} className="font-medium hover:underline">
                {product.name}
              </Link>
              <span className="text-sm text-zinc-600 dark:text-zinc-400">
                {formatCents(product.price)} each · {product.stock} in stock
              </span>
            </div>
            <div className="flex items-start gap-4">
              <QuantityForm
                action={updateCartItemAction.bind(null, product.id)}
                defaultQuantity={quantity}
                submitLabel="Update"
              />
              <span className="w-24 py-2 text-right font-mono">{formatCents(subtotal)}</span>
              <form action={removeCartItemAction.bind(null, product.id)}>
                <button
                  type="submit"
                  className="py-2 text-sm text-zinc-600 hover:underline dark:text-zinc-400"
                >
                  Remove
                </button>
              </form>
            </div>
          </li>
        ))}
      </ul>
      <div className="flex items-baseline justify-between text-lg">
        <span className="font-medium">Total</span>
        <span className="font-mono">{formatCents(data.total)}</span>
      </div>
      <ActionButton action={checkoutAction} label="Check out" pendingLabel="Placing order…" />
    </div>
  );
}

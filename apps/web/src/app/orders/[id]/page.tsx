import Link from "next/link";
import { Suspense } from "react";

import { ActionButton } from "@/components/action-button";
import { OrderStatusBadge } from "@/components/order-status-badge";
import { requireUser } from "@/lib/auth";
import { formatDate } from "@/lib/dates";
import { formatCents } from "@/lib/money";
import { NEXT_STATUS, canCancel, getOrderOrNotFound } from "@/lib/orders";

import { cancelOrderAction, updateOrderStatusAction } from "../actions";

export default function OrderPage(props: PageProps<"/orders/[id]">) {
  return (
    <div className="flex flex-col gap-6">
      <Link href="/orders" className="text-sm text-zinc-600 hover:underline dark:text-zinc-400">
        ← All orders
      </Link>
      <Suspense fallback={<div className="h-48 animate-pulse rounded-lg bg-zinc-100 dark:bg-zinc-900" />}>
        <OrderDetails params={props.params} />
      </Suspense>
    </div>
  );
}

async function OrderDetails({ params }: { params: PageProps<"/orders/[id]">["params"] }) {
  const user = await requireUser();
  const order = await getOrderOrNotFound((await params).id);
  const next = user.role === "admin" ? NEXT_STATUS[order.status] : undefined;

  return (
    <article className="flex flex-col gap-6">
      <div className="flex flex-col gap-2">
        <div className="flex items-center gap-3">
          <h1 className="text-3xl font-semibold tracking-tight">Order #{order.id}</h1>
          <OrderStatusBadge status={order.status} />
        </div>
        <p className="text-sm text-zinc-600 dark:text-zinc-400">
          Placed {formatDate(order.created_at)}
          {user.role === "admin" && ` by ${order.user.name} (${order.user.email})`}
        </p>
      </div>

      <table className="w-full text-left text-sm">
        <thead className="border-b border-zinc-200 text-zinc-500 dark:border-zinc-800">
          <tr>
            <th className="py-2 font-medium">Product</th>
            <th className="py-2 text-right font-medium">Price</th>
            <th className="py-2 text-right font-medium">Qty</th>
            <th className="py-2 text-right font-medium">Subtotal</th>
          </tr>
        </thead>
        <tbody className="divide-y divide-zinc-200 dark:divide-zinc-800">
          {order.items.map((item) => (
            <tr key={item.product_id}>
              <td className="py-2">{item.product_name}</td>
              <td className="py-2 text-right font-mono">{formatCents(item.unit_price)}</td>
              <td className="py-2 text-right">{item.quantity}</td>
              <td className="py-2 text-right font-mono">{formatCents(item.subtotal)}</td>
            </tr>
          ))}
        </tbody>
        <tfoot className="border-t border-zinc-200 text-base dark:border-zinc-800">
          <tr>
            <td colSpan={3} className="py-3 font-medium">
              Total
            </td>
            <td className="py-3 text-right font-mono">{formatCents(order.total)}</td>
          </tr>
        </tfoot>
      </table>
      <p className="text-xs text-zinc-500">Prices are as of checkout, even if the product has changed since.</p>

      {(next || canCancel(order.status)) && (
        <div className="flex flex-wrap items-start gap-3">
          {next && (
            <ActionButton
              action={updateOrderStatusAction.bind(null, order.id, next.status)}
              label={next.label}
              pendingLabel="Saving…"
            />
          )}
          {canCancel(order.status) && (
            <ActionButton
              action={cancelOrderAction.bind(null, order.id)}
              label="Cancel order"
              pendingLabel="Cancelling…"
              confirmText="Cancel this order? Its items go back in stock."
              variant="danger"
            />
          )}
        </div>
      )}
    </article>
  );
}

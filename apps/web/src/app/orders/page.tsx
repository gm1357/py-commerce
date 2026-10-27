import { ordersListOrders } from "api-client";
import Link from "next/link";
import { Suspense } from "react";

import { Notice } from "@/components/notice";
import { OrderStatusBadge } from "@/components/order-status-badge";
import { Pagination } from "@/components/pagination";
import { getSessionToken, requireUser } from "@/lib/auth";
import { formatDate } from "@/lib/dates";
import { formatCents } from "@/lib/money";

export default function OrdersPage(props: PageProps<"/orders">) {
  return (
    <div className="flex flex-col gap-8">
      <h1 className="text-3xl font-semibold tracking-tight">Orders</h1>
      <Suspense fallback={<div className="h-48 animate-pulse rounded-lg bg-zinc-100 dark:bg-zinc-900" />}>
        <OrderList searchParams={props.searchParams} />
      </Suspense>
    </div>
  );
}

async function OrderList({ searchParams }: { searchParams: PageProps<"/orders">["searchParams"] }) {
  const user = await requireUser();
  const pageParam = Number((await searchParams).page);
  const page = Number.isInteger(pageParam) && pageParam >= 1 ? pageParam : 1;

  const { data } = await ordersListOrders({ query: { page }, auth: await getSessionToken() });
  if (!data) throw new Error("Failed to load orders");
  if (data.total === 0) return <Notice>No orders yet.</Notice>;
  if (data.items.length === 0) {
    return (
      <Notice>
        Page {page} doesn&apos;t exist.{" "}
        <Link href="/orders" className="underline">
          Go to page 1
        </Link>
      </Notice>
    );
  }

  return (
    <div className="flex flex-col gap-6">
      {user.role === "admin" && (
        <p className="text-sm text-zinc-600 dark:text-zinc-400">Showing orders from every customer.</p>
      )}
      <ul className="flex flex-col gap-3">
        {data.items.map((order) => (
          <li key={order.id}>
            <Link
              href={`/orders/${order.id}`}
              className="flex flex-wrap items-center justify-between gap-3 rounded-lg border border-zinc-200 p-4 transition-colors hover:border-zinc-400 dark:border-zinc-800 dark:hover:border-zinc-600"
            >
              <div className="flex flex-col gap-1">
                <div className="flex items-center gap-2">
                  <span className="font-medium">Order #{order.id}</span>
                  <OrderStatusBadge status={order.status} />
                </div>
                <span className="text-sm text-zinc-600 dark:text-zinc-400">
                  {formatDate(order.created_at)} · {order.items.length}{" "}
                  {order.items.length === 1 ? "item" : "items"}
                  {user.role === "admin" && ` · ${order.user.name} (${order.user.email})`}
                </span>
              </div>
              <span className="font-mono">{formatCents(order.total)}</span>
            </Link>
          </li>
        ))}
      </ul>
      <Pagination page={data.page} pages={data.pages} basePath="/orders" />
    </div>
  );
}

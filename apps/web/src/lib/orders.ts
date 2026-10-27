import { ordersGetOrder, type OrderOut, type OrderStatus } from "api-client";
import { notFound, redirect } from "next/navigation";

import { getSessionToken } from "@/lib/auth";

/** Load an order for a `[id]` route segment. Someone else's order is a 404, same as the API. */
export async function getOrderOrNotFound(idParam: string): Promise<OrderOut> {
  if (!/^\d+$/.test(idParam)) notFound();

  const { data, response } = await ordersGetOrder({
    path: { order_id: Number(idParam) },
    auth: await getSessionToken(),
  });
  if (response?.status === 401) redirect("/signin");
  if (response?.status === 404) notFound();
  if (!data) throw new Error(`Failed to load order ${idParam}`);
  return data;
}

/** Statuses an order can still be cancelled from (mirrors the API's transition rules). */
export function canCancel(status: OrderStatus): boolean {
  return status === "pending" || status === "paid";
}

/** The next step an admin can move an order to, if any. */
export const NEXT_STATUS: Partial<Record<OrderStatus, { status: OrderStatus; label: string }>> = {
  pending: { status: "paid", label: "Mark paid" },
  paid: { status: "shipped", label: "Mark shipped" },
};

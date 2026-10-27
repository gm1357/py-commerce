"use server";

import { ordersCancelOrder, ordersUpdateOrderStatus, type OrderStatus } from "api-client";
import { revalidatePath } from "next/cache";
import { redirect } from "next/navigation";

import type { ActionState } from "@/components/action-button";
import { getSessionToken } from "@/lib/auth";
import { apiMessage } from "@/lib/errors";

async function finish(
  id: number,
  { error, response }: { error?: unknown; response?: Response },
): Promise<ActionState> {
  if (response?.status === 401) redirect("/signin");
  if (response?.status === 403) return { message: "Only admins can change an order's status." };
  // 409: the move isn't allowed from the current status (e.g. it shipped meanwhile).
  if (error) return { message: apiMessage(error, "Couldn't update the order. Please try again.") };

  revalidatePath("/orders");
  revalidatePath(`/orders/${id}`);
  return {};
}

export async function cancelOrderAction(id: number): Promise<ActionState> {
  const result = await ordersCancelOrder({
    path: { order_id: id },
    auth: await getSessionToken(),
  });
  return finish(id, result);
}

export async function updateOrderStatusAction(
  id: number,
  status: OrderStatus,
): Promise<ActionState> {
  const result = await ordersUpdateOrderStatus({
    path: { order_id: id },
    body: { status },
    auth: await getSessionToken(),
  });
  return finish(id, result);
}

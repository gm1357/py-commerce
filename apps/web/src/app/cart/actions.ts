"use server";

import { cartRemoveCartItem, cartSetCartItem, ordersCheckout } from "api-client";
import { revalidatePath } from "next/cache";
import { redirect } from "next/navigation";

import type { ActionState } from "@/components/action-button";
import { getSessionToken } from "@/lib/auth";
import { apiMessage } from "@/lib/errors";

export type CartActionState = ActionState;

/** PUT the quantity. Returns an error message, or nothing on success. */
async function setQuantity(productId: number, formData: FormData): Promise<string | undefined> {
  const { error, response } = await cartSetCartItem({
    path: { product_id: productId },
    body: { quantity: Number(formData.get("quantity")) },
    auth: await getSessionToken(),
  });
  if (response?.status === 401) redirect("/signin");
  if (response?.status === 422) return "Choose a quantity from 1 to 99.";
  if (error) return apiMessage(error, "Couldn't update your cart. Please try again.");
  revalidatePath("/cart");
}

/** From the product page. The API sets the quantity (it doesn't add to what's there). */
export async function addToCartAction(
  productId: number,
  _prev: CartActionState,
  formData: FormData,
): Promise<CartActionState> {
  const message = await setQuantity(productId, formData);
  if (message) return { message };
  redirect("/cart");
}

export async function updateCartItemAction(
  productId: number,
  _prev: CartActionState,
  formData: FormData,
): Promise<CartActionState> {
  return { message: await setQuantity(productId, formData) };
}

export async function removeCartItemAction(productId: number): Promise<void> {
  const { error, response } = await cartRemoveCartItem({
    path: { product_id: productId },
    auth: await getSessionToken(),
  });
  if (response?.status === 401) redirect("/signin");
  if (error) throw new Error(`Failed to remove product ${productId} from the cart`);
  revalidatePath("/cart");
}

export async function checkoutAction(): Promise<CartActionState> {
  const { data, error, response } = await ordersCheckout({ auth: await getSessionToken() });
  if (response?.status === 401) redirect("/signin");
  // 409: empty cart, or something sold out since it went in the cart.
  if (!data) return { message: apiMessage(error, "Checkout failed. Please try again.") };

  revalidatePath("/cart");
  revalidatePath("/orders");
  redirect(`/orders/${data.id}`);
}

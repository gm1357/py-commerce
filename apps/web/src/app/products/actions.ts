"use server";

import {
  productsCreateProduct,
  productsDeleteProduct,
  productsUpdateProduct,
  type HttpValidationError,
  type ProductIn,
} from "api-client";
import { revalidatePath } from "next/cache";
import { redirect } from "next/navigation";

import { parseDollars } from "@/lib/money";

type Field = "name" | "description" | "price";

export type ProductFormState = {
  errors?: Partial<Record<Field, string>>;
  message?: string;
  // Echo the submitted values: React resets uncontrolled forms after an action,
  // so without these a validation error would wipe what the user typed.
  values?: Record<Field, string>;
};

type ParsedForm =
  | { ok: true; values: Record<Field, string>; body: ProductIn }
  | { ok: false; state: ProductFormState };

function parseForm(formData: FormData): ParsedForm {
  const values = {
    name: String(formData.get("name") ?? ""),
    description: String(formData.get("description") ?? ""),
    price: String(formData.get("price") ?? ""),
  };
  const price = parseDollars(values.price);
  if (price === null) {
    const errors = { price: "Enter a price like 12.99 (up to 2 decimals)." };
    return { ok: false, state: { values, errors } };
  }
  const body = { name: values.name, description: values.description.trim() || null, price };
  return { ok: true, values, body };
}

function toFormState(
  values: Record<Field, string>,
  error: HttpValidationError | undefined,
): ProductFormState {
  // FastAPI 422s look like { detail: [{ loc: ["body", "name"], msg: "..." }] }
  const errors: Partial<Record<Field, string>> = {};
  for (const issue of error?.detail ?? []) {
    const field = issue.loc.at(-1);
    if (field === "name" || field === "description" || field === "price") {
      errors[field] = issue.msg;
    }
  }
  if (Object.keys(errors).length > 0) return { values, errors };
  return { values, message: "Something went wrong saving the product. Please try again." };
}

export async function createProductAction(
  _prev: ProductFormState,
  formData: FormData,
): Promise<ProductFormState> {
  const parsed = parseForm(formData);
  if (!parsed.ok) return parsed.state;

  const { error } = await productsCreateProduct({ body: parsed.body });
  if (error) return toFormState(parsed.values, error);

  revalidatePath("/");
  redirect("/");
}

export async function updateProductAction(
  id: number,
  _prev: ProductFormState,
  formData: FormData,
): Promise<ProductFormState> {
  const parsed = parseForm(formData);
  if (!parsed.ok) return parsed.state;

  const { values, body } = parsed;
  const { error, response } = await productsUpdateProduct({ path: { product_id: id }, body });
  if (response?.status === 404) return { values, message: "This product no longer exists." };
  if (error) return toFormState(values, error);

  revalidatePath("/");
  revalidatePath(`/products/${id}`);
  redirect(`/products/${id}`);
}

export async function deleteProductAction(id: number): Promise<void> {
  const { error, response } = await productsDeleteProduct({ path: { product_id: id } });
  // 404 means it's already gone, which is what the user wanted.
  if (error && response?.status !== 404) throw new Error(`Failed to delete product ${id}`);

  revalidatePath("/");
  redirect("/");
}

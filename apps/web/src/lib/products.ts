import { productsGetProduct, type ProductOut } from "api-client";
import { notFound } from "next/navigation";

/** Load a product for a `[id]` route segment, rendering the not-found page when it doesn't exist. */
export async function getProductOrNotFound(idParam: string): Promise<ProductOut> {
  if (!/^\d+$/.test(idParam)) notFound();

  const { data, response } = await productsGetProduct({ path: { product_id: Number(idParam) } });
  if (response?.status === 404) notFound();
  if (!data) throw new Error(`Failed to load product ${idParam}`);
  return data;
}

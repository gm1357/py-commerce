import { Suspense } from "react";

import { ProductForm } from "@/components/product-form";
import { centsToDollarInput } from "@/lib/money";
import { requireAdmin } from "@/lib/auth";
import { getProductOrNotFound } from "@/lib/products";

import { updateProductAction } from "../../actions";

export default function EditProductPage(props: PageProps<"/products/[id]/edit">) {
  return (
    <div className="flex flex-col gap-6">
      <h1 className="text-3xl font-semibold tracking-tight">Edit product</h1>
      <Suspense fallback={<div className="h-80 animate-pulse rounded-lg bg-zinc-100 dark:bg-zinc-900" />}>
        <EditProductForm params={props.params} />
      </Suspense>
    </div>
  );
}

async function EditProductForm({ params }: { params: PageProps<"/products/[id]/edit">["params"] }) {
  await requireAdmin();
  const product = await getProductOrNotFound((await params).id);

  return (
    <ProductForm
      action={updateProductAction.bind(null, product.id)}
      initialValues={{
        name: product.name,
        description: product.description ?? "",
        price: centsToDollarInput(product.price),
        stock: String(product.stock),
      }}
      submitLabel="Save changes"
      cancelHref={`/products/${product.id}`}
    />
  );
}

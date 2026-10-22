import { ProductForm } from "@/components/product-form";

import { createProductAction } from "../actions";

export default function NewProductPage() {
  return (
    <div className="flex flex-col gap-6">
      <h1 className="text-3xl font-semibold tracking-tight">New product</h1>
      <ProductForm action={createProductAction} submitLabel="Create product" cancelHref="/" />
    </div>
  );
}

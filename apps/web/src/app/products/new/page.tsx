import { Suspense } from "react";

import { ProductForm } from "@/components/product-form";
import { requireAdmin } from "@/lib/auth";

import { createProductAction } from "../actions";

export default function NewProductPage() {
  return (
    <div className="flex flex-col gap-6">
      <h1 className="text-3xl font-semibold tracking-tight">New product</h1>
      <Suspense fallback={<div className="h-80 animate-pulse rounded-lg bg-zinc-100 dark:bg-zinc-900" />}>
        <NewProductForm />
      </Suspense>
    </div>
  );
}

async function NewProductForm() {
  await requireAdmin();

  return <ProductForm action={createProductAction} submitLabel="Create product" cancelHref="/" />;
}

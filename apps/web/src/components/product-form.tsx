"use client";

import Link from "next/link";
import { useActionState } from "react";

import type { ProductFormState } from "@/app/products/actions";
import { Field, inputClass } from "@/components/field";

type Values = { name: string; description: string; price: string };

type Props = {
  action: (state: ProductFormState, formData: FormData) => Promise<ProductFormState>;
  initialValues?: Values;
  submitLabel: string;
  cancelHref: string;
};

/** Shared by the create and edit pages; only the bound action and initial values differ. */
export function ProductForm({ action, initialValues, submitLabel, cancelHref }: Props) {
  const [state, formAction, pending] = useActionState(action, {});
  const values = state.values ?? initialValues;
  const errors = state.errors ?? {};

  return (
    <form action={formAction} className="flex flex-col gap-5">
      <Field label="Name" htmlFor="name" error={errors.name}>
        <input
          id="name"
          name="name"
          required
          maxLength={200}
          defaultValue={values?.name}
          aria-invalid={!!errors.name}
          className={inputClass}
        />
      </Field>

      <Field label="Description (optional)" htmlFor="description" error={errors.description}>
        <textarea
          id="description"
          name="description"
          rows={4}
          maxLength={2000}
          defaultValue={values?.description}
          aria-invalid={!!errors.description}
          className={inputClass}
        />
      </Field>

      <Field label="Price (USD)" htmlFor="price" error={errors.price}>
        <input
          id="price"
          name="price"
          required
          inputMode="decimal"
          placeholder="12.99"
          defaultValue={values?.price}
          aria-invalid={!!errors.price}
          className={inputClass}
        />
      </Field>

      {state.message && (
        <p role="alert" className="text-sm text-red-600 dark:text-red-400">
          {state.message}
        </p>
      )}

      <div className="flex items-center gap-3">
        <button
          type="submit"
          disabled={pending}
          className="rounded-md bg-zinc-900 px-4 py-2 font-medium text-white disabled:opacity-50 dark:bg-zinc-100 dark:text-zinc-900"
        >
          {pending ? "Saving…" : submitLabel}
        </button>
        <Link href={cancelHref} className="text-zinc-600 hover:underline dark:text-zinc-400">
          Cancel
        </Link>
      </div>
    </form>
  );
}

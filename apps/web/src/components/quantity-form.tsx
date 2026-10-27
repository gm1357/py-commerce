"use client";

import { useActionState, useId } from "react";

import type { CartActionState } from "@/app/cart/actions";
import { inputClass } from "@/components/field";

type Props = {
  action: (state: CartActionState, formData: FormData) => Promise<CartActionState>;
  defaultQuantity: number;
  submitLabel: string;
};

/** A quantity input plus a button. Used for "Add to cart" and for updating a cart line. */
export function QuantityForm({ action, defaultQuantity, submitLabel }: Props) {
  const [state, formAction, pending] = useActionState(action, {});
  const id = useId();

  return (
    <form action={formAction} className="flex flex-col gap-1.5">
      <div className="flex items-center gap-2">
        <label className="sr-only" htmlFor={id}>
          Quantity
        </label>
        <input
          id={id}
          name="quantity"
          type="number"
          required
          min={1}
          max={99}
          defaultValue={defaultQuantity}
          className={`${inputClass} w-20`}
        />
        <button
          type="submit"
          disabled={pending}
          className="rounded-md border border-zinc-300 px-3 py-2 text-sm font-medium hover:bg-zinc-100 disabled:opacity-50 dark:border-zinc-700 dark:hover:bg-zinc-900"
        >
          {pending ? "Saving…" : submitLabel}
        </button>
      </div>
      {state.message && (
        <p role="alert" className="text-sm text-red-600 dark:text-red-400">
          {state.message}
        </p>
      )}
    </form>
  );
}

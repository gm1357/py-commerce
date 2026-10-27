"use client";

import { useActionState } from "react";

export type ActionState = { message?: string };

type Props = {
  action: (state: ActionState) => Promise<ActionState>;
  label: string;
  pendingLabel: string;
  /** Ask before running the action, e.g. "Cancel this order?". */
  confirmText?: string;
  variant?: "primary" | "danger";
};

const variants = {
  primary:
    "bg-zinc-900 text-white dark:bg-zinc-100 dark:text-zinc-900",
  danger:
    "border border-red-300 text-red-700 hover:bg-red-50 dark:border-red-800 dark:text-red-400 dark:hover:bg-red-950",
};

/** A one-button form for a server action that can fail with a message (checkout, cancel…). */
export function ActionButton({ action, label, pendingLabel, confirmText, variant = "primary" }: Props) {
  const [state, formAction, pending] = useActionState(action, {});

  return (
    <form
      action={formAction}
      onSubmit={(event) => {
        if (confirmText && !confirm(confirmText)) event.preventDefault();
      }}
      className="flex flex-col gap-1.5"
    >
      <button
        type="submit"
        disabled={pending}
        className={`self-start rounded-md px-4 py-2 font-medium disabled:opacity-50 ${variants[variant]}`}
      >
        {pending ? pendingLabel : label}
      </button>
      {state.message && (
        <p role="alert" className="text-sm text-red-600 dark:text-red-400">
          {state.message}
        </p>
      )}
    </form>
  );
}

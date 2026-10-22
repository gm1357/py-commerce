"use client";

import { useActionState } from "react";

import type { AuthFormState } from "@/app/(auth)/actions";
import { Field, inputClass } from "@/components/field";

type Props = {
  action: (state: AuthFormState, formData: FormData) => Promise<AuthFormState>;
  mode: "signin" | "signup";
};

/** Shared by the sign-in and sign-up pages; sign-up adds a name field. */
export function AuthForm({ action, mode }: Props) {
  const [state, formAction, pending] = useActionState(action, {});
  const errors = state.errors ?? {};
  const submitLabel = mode === "signup" ? "Create account" : "Sign in";

  return (
    <form action={formAction} className="flex flex-col gap-5">
      {mode === "signup" && (
        <Field label="Name" htmlFor="name" error={errors.name}>
          <input
            id="name"
            name="name"
            required
            maxLength={100}
            autoComplete="name"
            defaultValue={state.values?.name}
            aria-invalid={!!errors.name}
            className={inputClass}
          />
        </Field>
      )}

      <Field label="Email" htmlFor="email" error={errors.email}>
        <input
          id="email"
          name="email"
          type="email"
          required
          autoComplete="email"
          defaultValue={state.values?.email}
          aria-invalid={!!errors.email}
          className={inputClass}
        />
      </Field>

      <Field label="Password" htmlFor="password" error={errors.password}>
        <input
          id="password"
          name="password"
          type="password"
          required
          minLength={mode === "signup" ? 8 : undefined}
          maxLength={128}
          autoComplete={mode === "signup" ? "new-password" : "current-password"}
          aria-invalid={!!errors.password}
          className={inputClass}
        />
      </Field>

      {state.message && (
        <p role="alert" className="text-sm text-red-600 dark:text-red-400">
          {state.message}
        </p>
      )}

      <button
        type="submit"
        disabled={pending}
        className="rounded-md bg-zinc-900 px-4 py-2 font-medium text-white disabled:opacity-50 dark:bg-zinc-100 dark:text-zinc-900"
      >
        {pending ? "Please wait…" : submitLabel}
      </button>
    </form>
  );
}

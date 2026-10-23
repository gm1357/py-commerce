import Link from "next/link";

import { AuthForm } from "@/components/auth-form";

import { signinAction } from "../actions";

export default function SigninPage() {
  return (
    <div className="mx-auto flex w-full max-w-sm flex-col gap-6">
      <h1 className="text-3xl font-semibold tracking-tight">Sign in</h1>
      <AuthForm action={signinAction} mode="signin" />
      <p className="text-sm text-zinc-600 dark:text-zinc-400">
        No account yet?{" "}
        <Link href="/signup" className="underline">
          Sign up
        </Link>
      </p>
    </div>
  );
}

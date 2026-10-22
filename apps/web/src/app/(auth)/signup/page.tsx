import Link from "next/link";

import { AuthForm } from "@/components/auth-form";

import { signupAction } from "../actions";

export default function SignupPage() {
  return (
    <div className="mx-auto flex w-full max-w-sm flex-col gap-6">
      <h1 className="text-3xl font-semibold tracking-tight">Create an account</h1>
      <AuthForm action={signupAction} mode="signup" />
      <p className="text-sm text-zinc-600 dark:text-zinc-400">
        Already have an account?{" "}
        <Link href="/signin" className="underline">
          Sign in
        </Link>
      </p>
    </div>
  );
}

"use server";

import { authLogin, authLogout, authSignup, type HttpValidationError } from "api-client";
import { cookies } from "next/headers";
import { redirect } from "next/navigation";

import { SESSION_COOKIE, getSessionToken, saveSessionCookie } from "@/lib/auth";

type Field = "name" | "email" | "password";

export type AuthFormState = {
  errors?: Partial<Record<Field, string>>;
  message?: string;
  // Echoed back so an error doesn't wipe the form (see ProductFormState). Never the password.
  values?: { name: string; email: string };
};

function readForm(formData: FormData) {
  return {
    name: String(formData.get("name") ?? ""),
    email: String(formData.get("email") ?? ""),
    password: String(formData.get("password") ?? ""),
  };
}

function toFormState(
  values: AuthFormState["values"],
  error: HttpValidationError | undefined,
): AuthFormState {
  // FastAPI 422s look like { detail: [{ loc: ["body", "email"], msg: "..." }] }
  const errors: Partial<Record<Field, string>> = {};
  for (const issue of Array.isArray(error?.detail) ? error.detail : []) {
    const field = issue.loc.at(-1);
    if (field === "name" || field === "email" || field === "password") errors[field] = issue.msg;
  }
  if (Object.keys(errors).length > 0) return { values, errors };
  return { values, message: "Something went wrong. Please try again." };
}

export async function signupAction(
  _prev: AuthFormState,
  formData: FormData,
): Promise<AuthFormState> {
  const { name, email, password } = readForm(formData);
  const values = { name, email };

  const { error, response } = await authSignup({ body: { name, email, password } });
  if (response?.status === 409) {
    return { values, errors: { email: "An account with this email already exists." } };
  }
  if (error || !response) return toFormState(values, error);

  await saveSessionCookie(response);
  redirect("/");
}

export async function signinAction(
  _prev: AuthFormState,
  formData: FormData,
): Promise<AuthFormState> {
  const { email, password } = readForm(formData);
  const values = { name: "", email };

  const { error, response } = await authLogin({ body: { email, password } });
  if (response?.status === 401) return { values, message: "Invalid email or password." };
  if (error || !response) return toFormState(values, error);

  await saveSessionCookie(response);
  redirect("/");
}

export async function signoutAction(): Promise<void> {
  const token = await getSessionToken();
  if (token) await authLogout({ auth: token });

  (await cookies()).delete(SESSION_COOKIE);
  redirect("/");
}

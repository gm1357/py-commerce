import { authGetMe, type UserOut } from "api-client";
import { cookies } from "next/headers";
import { redirect } from "next/navigation";
import { cache } from "react";

// The API's session cookie. The web app calls the API from the server, so it keeps the same
// cookie on its own domain and hands the token back to the API (`auth` option) when needed.
export const SESSION_COOKIE = "session_id";

export async function getSessionToken(): Promise<string | undefined> {
  return (await cookies()).get(SESSION_COOKIE)?.value;
}

/** The signed-in user, or null. Cached per request, so several components cost one API call. */
export const getCurrentUser = cache(async (): Promise<UserOut | null> => {
  const token = await getSessionToken();
  if (!token) return null;
  const { data } = await authGetMe({ auth: token });
  return data ?? null;
});

/** For pages that need a signed-in user, like the cart. */
export async function requireUser(): Promise<UserOut> {
  const user = await getCurrentUser();
  if (!user) redirect("/signin");
  return user;
}

/** For admin-only pages. The API enforces the same rule; this just avoids showing a dead end. */
export async function requireAdmin(): Promise<UserOut> {
  const user = await requireUser();
  if (user.role !== "admin") redirect("/");
  return user;
}

/**
 * Copy the session cookie from an API signup/login response onto the browser. The response
 * reached the Next server, not the browser, so its Set-Cookie would otherwise be lost.
 */
export async function saveSessionCookie(response: Response): Promise<void> {
  const header = response.headers
    .getSetCookie()
    .find((cookie) => cookie.startsWith(`${SESSION_COOKIE}=`));
  if (!header) throw new Error("API response did not set a session cookie");

  // e.g. "session_id=abc123; HttpOnly; Max-Age=604800; Path=/; SameSite=lax"
  const [pair, ...attributes] = header.split(";").map((part) => part.trim());
  const maxAge = attributes.find((attr) => attr.toLowerCase().startsWith("max-age="));

  (await cookies()).set(SESSION_COOKIE, pair.slice(SESSION_COOKIE.length + 1), {
    httpOnly: true,
    sameSite: "lax",
    secure: process.env.NODE_ENV === "production",
    path: "/",
    maxAge: maxAge ? Number(maxAge.split("=")[1]) : undefined,
  });
}

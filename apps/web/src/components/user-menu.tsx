import Link from "next/link";

import { signoutAction } from "@/app/(auth)/actions";
import { getCurrentUser } from "@/lib/auth";

/** Reads the session, so it must render inside a <Suspense> boundary. */
export async function UserMenu() {
  const user = await getCurrentUser();

  if (!user) {
    return (
      <nav className="flex items-center gap-4 text-sm">
        <Link href="/signin" className="hover:underline">
          Sign in
        </Link>
        <Link
          href="/signup"
          className="rounded-md bg-zinc-900 px-3 py-1.5 font-medium text-white dark:bg-zinc-100 dark:text-zinc-900"
        >
          Sign up
        </Link>
      </nav>
    );
  }

  return (
    <div className="flex items-center gap-3 text-sm">
      <Link href="/cart" className="hover:underline">
        Cart
      </Link>
      <Link href="/orders" className="hover:underline">
        Orders
      </Link>
      <span className="text-zinc-400 dark:text-zinc-600" aria-hidden>
        |
      </span>
      <span>{user.name}</span>
      {user.role === "admin" && (
        <span className="rounded bg-amber-100 px-1.5 py-0.5 text-xs font-medium text-amber-800 dark:bg-amber-950 dark:text-amber-300">
          admin
        </span>
      )}
      <form action={signoutAction}>
        <button type="submit" className="text-zinc-600 hover:underline dark:text-zinc-400">
          Sign out
        </button>
      </form>
    </div>
  );
}

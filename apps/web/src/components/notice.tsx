/** A dashed box for empty or missing states ("No products yet", "Your cart is empty"). */
export function Notice({ children }: { children: React.ReactNode }) {
  return (
    <p className="rounded-lg border border-dashed border-zinc-300 p-8 text-center text-zinc-600 dark:border-zinc-700 dark:text-zinc-400">
      {children}
    </p>
  );
}

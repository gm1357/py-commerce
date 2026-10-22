const usd = new Intl.NumberFormat("en-US", { style: "currency", currency: "USD" });

export function formatCents(cents: number): string {
  return usd.format(cents / 100);
}

/** "12.9" -> 1290. Parses digits instead of using float math, so "0.29" is exactly 29. */
export function parseDollars(input: string): number | null {
  const match = /^(\d+)(?:\.(\d{1,2}))?$/.exec(input.trim());
  if (!match) return null;
  const [, dollars, fraction = ""] = match;
  return Number(dollars) * 100 + Number(fraction.padEnd(2, "0"));
}

/** 1290 -> "12.90", for pre-filling the price input. */
export function centsToDollarInput(cents: number): string {
  return (cents / 100).toFixed(2);
}

/**
 * The message from an API error like `{ detail: "Your cart is empty" }`. FastAPI sends a string
 * `detail` for HTTPException and domain errors (404, 409), but a list for 422 validation errors,
 * so anything that isn't a string falls back to `fallback`.
 */
export function apiMessage(error: unknown, fallback: string): string {
  const detail = (error as { detail?: unknown } | undefined)?.detail;
  return typeof detail === "string" ? detail : fallback;
}

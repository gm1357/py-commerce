const dateTime = new Intl.DateTimeFormat("en-US", { dateStyle: "medium", timeStyle: "short" });

export function formatDate(iso: string): string {
  return dateTime.format(new Date(iso));
}

import type { Score } from "./types";

const ZONE = "Europe/Warsaw";
const kickoffFormat = new Intl.DateTimeFormat("pl-PL", {
  timeZone: ZONE, weekday: "short", day: "2-digit", month: "2-digit", hour: "2-digit", minute: "2-digit",
});
const timeFormat = new Intl.DateTimeFormat("pl-PL", { timeZone: ZONE, hour: "2-digit", minute: "2-digit" });
const dateFormat = new Intl.DateTimeFormat("pl-PL", { timeZone: ZONE, day: "2-digit", month: "2-digit", year: "numeric" });
const shortDate = new Intl.DateTimeFormat("pl-PL", { timeZone: ZONE, day: "2-digit", month: "2-digit", year: "2-digit" });
const numberFormat = new Intl.NumberFormat("pl-PL", { maximumFractionDigits: 2 });

export const kickoff = (iso: string) => kickoffFormat.format(new Date(iso));
export const time = (iso: string) => timeFormat.format(new Date(iso));
export const date = (iso: string) => dateFormat.format(new Date(iso));
export const dateShort = (iso: string) => shortDate.format(new Date(iso));
export const num = (value: number | null | undefined) => (value === null || value === undefined ? "—" : numberFormat.format(value));

/** "1:1 (pd. 1:2)" or "1:1 (k. 4:5)"; the 90-minute score always comes first. */
export function score(s: Score | null, flip = false): string {
  if (!s) return "—";
  const pick = (h: number | null, a: number | null) => (flip ? `${a}:${h}` : `${h}:${a}`);
  let text = pick(s.home_90, s.away_90);
  if (s.home_aet !== null && s.away_aet !== null && s.home_pens === null) text += ` (pd. ${pick(s.home_aet, s.away_aet)})`;
  if (s.home_pens !== null && s.away_pens !== null) text += ` (k. ${pick(s.home_pens, s.away_pens)})`;
  return text;
}

export function days(n: number | null): string {
  if (n === null) return "—";
  return n === 1 ? "1 dzień" : `${n} dni`;
}

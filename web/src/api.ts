import type { DayResponse, Filters, MatchBundle } from "./types";

export class ApiError extends Error {
  constructor(public status: number, message: string) {
    super(message);
  }
}

async function getJSON<T>(path: string, signal?: AbortSignal): Promise<T> {
  const response = await fetch(path, { signal, headers: { Accept: "application/json" } });
  if (!response.ok) throw new ApiError(response.status, `HTTP ${response.status}`);
  return (await response.json()) as T;
}

export function fetchDay(date: string | null, signal?: AbortSignal): Promise<DayResponse> {
  const query = date ? `?date=${encodeURIComponent(date)}` : "";
  return getJSON<DayResponse>(`/api/v1/matches${query}`, signal);
}

export function fetchMatch(id: string, filters: Filters, signal?: AbortSignal): Promise<MatchBundle> {
  const query = new URLSearchParams({
    window: String(filters.window),
    split: filters.split,
    period: filters.period,
    competitions: filters.competitions,
  });
  return getJSON<MatchBundle>(`/api/v1/matches/${encodeURIComponent(id)}?${query}`, signal);
}

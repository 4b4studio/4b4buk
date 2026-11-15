// Polish UI copy. The backend returns codes and parameters only, so wording can
// change (or gain languages) without touching the statistics engine.
import type { Reason, TeamRef } from "./types";

type Teams = Record<string, TeamRef>;
type Names = { team: (id: string) => string; competition: (id: string) => string };

const numberFormat = new Intl.NumberFormat("pl-PL", { maximumFractionDigits: 2 });
// Numeric parameters use Polish formatting (decimal comma).
const p = (reason: Reason, key: string) => {
  const value = reason.params[key];
  return typeof value === "number" ? numberFormat.format(value) : value;
};

const REASONS: Record<string, (r: Reason, n: Names) => string> = {
  FOLLOWED_TEAM: (r, n) => `Obserwujesz: ${n.team(String(p(r, "team")))}`,
  FOLLOWED_COMPETITION: (r, n) => `Obserwowane rozgrywki: ${n.competition(String(p(r, "competition")))}`,
  TOP_CLASH: (r) => `Mecz czołówki: ${p(r, "pos_home")}. vs ${p(r, "pos_away")}. miejsce`,
  RELEGATION_BATTLE: (r) => `Dół tabeli: ${p(r, "pos_home")}. vs ${p(r, "pos_away")}. miejsce`,
  CLOSE_IN_TABLE: (r) => `Blisko w tabeli (różnica ${p(r, "gap")} pkt)`,
  HIGH_SCORING: (r) => `Bramkowe ostatnie mecze obu drużyn: śr. ${p(r, "avg")} gola na mecz (ost. 10)`,
  KNOCKOUT: () => "Mecz pucharowy",
  DISCOVERY: (r, n) => `Spoza Twoich zainteresowań: ${n.competition(String(p(r, "competition")))}`,
  SHORT_REST: (r, n) => `${n.team(String(p(r, "team")))}: tylko ${p(r, "days")} dni od poprzedniego meczu`,
  REST_GAP: (r, n) => `${n.team(String(p(r, "team")))} ma ${p(r, "diff")} dni więcej odpoczynku`,
  CONTINENTAL_BEFORE: (r, n) => `${n.team(String(p(r, "team")))}: mecz europejskiego pucharu ${p(r, "days")} dni wcześniej`,
  CONTINENTAL_AFTER: (r, n) => `${n.team(String(p(r, "team")))}: europejski puchar za ${p(r, "days")} dni`,
  CUP_BEFORE: (r, n) => `${n.team(String(p(r, "team")))}: puchar krajowy ${p(r, "days")} dni wcześniej`,
  CUP_AFTER: (r, n) => `${n.team(String(p(r, "team")))}: puchar krajowy za ${p(r, "days")} dni`,
  PREV_EXTRA_TIME: (r, n) => `${n.team(String(p(r, "team")))}: dogrywka w poprzednim meczu`,
  PREV_SHOOTOUT: (r, n) => `${n.team(String(p(r, "team")))}: dogrywka i karne w poprzednim meczu`,
  NEW_COACH: (r, n) => `${n.team(String(p(r, "team")))}: nowy trener od ${p(r, "days")} dni (mała próba)`,
  KEY_ABSENCES: (r, n) => `${n.team(String(p(r, "team")))}: potwierdzone braki kluczowych zawodników (${p(r, "count")})`,
  HIGH_CORNERS: (r) => `Dużo rożnych w układzie dom/wyjazd: ok. ${p(r, "total")} łącznie (opis historii)`,
  LOW_CORNERS: (r) => `Mało rożnych w układzie dom/wyjazd: ok. ${p(r, "total")} łącznie (opis historii)`,
  HIGH_CARDS: (r) => `Dużo kartek obu drużyn: ok. ${p(r, "total")} łącznie na mecz (opis historii)`,
  H2H_STALE: (r) => `Ostatni mecz bezpośredni ${p(r, "days")} dni temu — mała wartość informacyjna`,
  H2H_NONE: () => "Drużyny wcześniej nie grały ze sobą",
  COACH_CHANGED_SINCE_LAST: () => "Od ostatniego H2H zmienił się trener",
  SMALL_SAMPLE: () => "Mała próba danych dla co najmniej jednej drużyny",
};

export function reasonText(reason: Reason, teams: Teams, competitions: Record<string, { name: string }>): string {
  const names: Names = {
    team: (id) => teams[id]?.name ?? id,
    competition: (id) => competitions[id]?.name ?? id,
  };
  return REASONS[reason.code]?.(reason, names) ?? reason.code;
}

export const QUALITY: Record<string, string> = {
  DEMO_DATA: "Dane demonstracyjne: fikcyjne drużyny i wyniki",
  MISSING_STATS: "Brak statystyk dla części meczów — pominięte w średnich, widoczne na liście",
  EXCLUDED_EXTRA_TIME: "Statystyki obejmujące dogrywkę pominięte w trybie „90 min”",
  SMALL_SAMPLE: "Mała próba (mniej niż 5 meczów) w części porównań",
  ABSENCES_NO_DATA: "Brak danych o absencjach dla co najmniej jednej drużyny",
  LINEUPS_NOT_CONFIRMED: "Składy nie są jeszcze potwierdzone",
  H2H_STALE: "Ostatni mecz bezpośredni ponad 2 lata temu",
  H2H_SMALL_SAMPLE: "Mniej niż 3 mecze bezpośrednie",
  H2H_NONE: "Brak meczów bezpośrednich",
  COACH_CHANGED_SINCE_LAST: "Zmiana trenera od ostatniego H2H",
};

export const METRIC: Record<string, string> = {
  "goals:for": "Gole zdobyte",
  "goals:against": "Gole stracone",
  "corners:for": "Rożne wykonane",
  "corners:against": "Rożne rywala",
  "cards:for": "Kartki (ż+cz)",
  "shots:for": "Strzały",
  "shots_on_target:for": "Strzały celne",
};

export const FLAG: Record<string, string> = {
  SHORT_REST: "Krótki odpoczynek",
  CONTINENTAL_BEFORE: "Puchar europejski przed",
  CONTINENTAL_AFTER: "Puchar europejski po",
  CUP_BEFORE: "Puchar krajowy przed",
  CUP_AFTER: "Puchar krajowy po",
  PREV_EXTRA_TIME: "Dogrywka w poprzednim",
  PREV_SHOOTOUT: "Dogrywka i karne w poprzednim",
  CONGESTED: "Natłok meczów",
};

export const EXCLUDED: Record<string, string> = {
  missing_stat: "brak statystyki",
  stats_include_extra_time: "statystyki z dogrywką",
};

export const ABSENCE_REASON = { injury: "kontuzja", suspension: "zawieszenie", other: "inny powód" } as const;
export const ABSENCE_STATUS = { confirmed: "potwierdzone", doubtful: "niepewne" } as const;
export const SOURCE: Record<string, string> = {
  club_statement: "komunikat klubu",
  competition_suspensions: "lista zawieszeń",
  press_conference: "konferencja prasowa",
};
export const LINEUP = { not_available: "brak", predicted: "przewidywany", confirmed: "potwierdzony" } as const;
export const RISK = { low: "niskie", medium: "średnie", high: "wysokie" } as const;
export const VENUE = { home: "D", away: "W", neutral: "N" } as const;
export const KIND: Record<string, string> = { league: "liga", domestic_cup: "puchar krajowy", continental: "puchar europejski" };

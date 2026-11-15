import type { ReactNode } from "react";
import * as fmt from "../format";
import { reasonText } from "../i18n";
import type { CompetitionRef, DataInfo, FormEntry, Reason, TeamRef } from "../types";

export function DataBanner({ data }: { data: DataInfo }) {
  if (!data.is_demo) {
    return <p className="data-note">Dane: {data.source}, stan na {fmt.kickoff(data.as_of)}</p>;
  }
  return (
    <p className="demo-banner" role="note">
      <strong>DEMO</strong> — fikcyjne drużyny, zawodnicy i wyniki. Stan danych: {fmt.kickoff(data.as_of)}.
    </p>
  );
}

export function ReasonList({
  reasons,
  teams,
  competitions,
  limit,
  tone = "info",
}: {
  reasons: Reason[];
  teams: Record<string, TeamRef>;
  competitions: Record<string, CompetitionRef | { name: string }>;
  limit?: number;
  tone?: "info" | "warn";
}) {
  const shown = limit ? reasons.slice(0, limit) : reasons;
  if (!shown.length) return null;
  return (
    <ul className={`reasons reasons-${tone}`}>
      {shown.map((reason, index) => (
        <li key={`${reason.code}-${index}`}>{reasonText(reason, teams, competitions)}</li>
      ))}
    </ul>
  );
}

const RESULT_LABEL = { W: "Z", D: "R", L: "P" } as const;

export function FormStrip({ entries, teams }: { entries: FormEntry[]; teams: Record<string, TeamRef> }) {
  if (!entries.length) return <span className="muted">brak meczów</span>;
  return (
    <ol className="form-strip" aria-label="Forma, od najnowszego meczu">
      {entries.map((entry) => {
        const extra = entry.decided_by !== "regulation";
        const title =
          `${fmt.date(entry.kickoff)} ${teams[entry.opponent_id]?.name ?? entry.opponent_id} ` +
          `${entry.goals_for_90}:${entry.goals_against_90}` +
          (extra ? ` po 90 min; ostatecznie ${RESULT_LABEL[entry.final_result]} (${entry.decided_by === "penalties" ? "karne" : "dogrywka"})` : "");
        return (
          <li key={entry.match_id} className={`result result-${entry.result_90}`} title={title}>
            {RESULT_LABEL[entry.result_90]}
            {extra ? <sup>{entry.decided_by === "penalties" ? "k" : "d"}</sup> : null}
          </li>
        );
      })}
    </ol>
  );
}

export function Segmented<T extends string | number>({
  label,
  value,
  options,
  onChange,
}: {
  label: string;
  value: T;
  options: { value: T; label: string }[];
  onChange: (value: T) => void;
}) {
  return (
    <div className="segmented" role="group" aria-label={label}>
      <span className="segmented-label">{label}</span>
      {options.map((option) => (
        <button
          key={String(option.value)}
          type="button"
          aria-pressed={option.value === value}
          className={option.value === value ? "active" : ""}
          onClick={() => onChange(option.value)}
        >
          {option.label}
        </button>
      ))}
    </div>
  );
}

export function Section({ title, children, aside }: { title: string; children: ReactNode; aside?: ReactNode }) {
  return (
    <section className="card">
      <header className="card-header">
        <h2>{title}</h2>
        {aside}
      </header>
      {children}
    </section>
  );
}

export function Status({ error, loading }: { error: string | null; loading: boolean }) {
  if (error) return <p className="status status-error">Nie udało się pobrać danych ({error}). Spróbuj ponownie.</p>;
  if (loading) return <p className="status">Ładowanie…</p>;
  return null;
}

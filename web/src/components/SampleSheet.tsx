import { useEffect, useRef } from "react";
import * as fmt from "../format";
import { EXCLUDED, KIND, METRIC, VENUE } from "../i18n";
import type { Average, CompetitionRef, TeamRef } from "../types";

// Every average can be opened to show exactly which matches it uses.
export function SampleSheet({
  average,
  teamName,
  teams,
  competitions,
  onClose,
}: {
  average: Average;
  teamName: string;
  teams: Record<string, TeamRef>;
  competitions: Record<string, CompetitionRef>;
  onClose: () => void;
}) {
  const dialog = useRef<HTMLDialogElement>(null);
  useEffect(() => {
    const element = dialog.current;
    if (element && !element.open) element.showModal();
  }, []);
  const label = METRIC[`${average.metric}:${average.perspective}`] ?? average.metric;
  const filter = average.sample_filter;
  return (
    <dialog ref={dialog} className="sheet" onClose={onClose} aria-labelledby="sheet-title">
      <header className="sheet-header">
        <div>
          <h3 id="sheet-title">
            {teamName}: {label}
          </h3>
          <p className="muted">
            Średnia {fmt.num(average.value)} z {average.n_used} meczów (rozważono {average.n_considered}; okno {filter.window},{" "}
            {filter.venue === "all" ? "dom i wyjazd" : filter.venue === "home" ? "tylko dom" : "tylko wyjazd"},{" "}
            {filter.period === "regulation" ? "90 min" : "z dogrywką"})
          </p>
        </div>
        <button type="button" className="icon-button" onClick={() => dialog.current?.close()} aria-label="Zamknij">
          ×
        </button>
      </header>
      <table className="sample-table">
        <thead>
          <tr>
            <th>Data</th>
            <th>Rywal</th>
            <th>Rozgrywki</th>
            <th>Wynik 90'</th>
            <th>Wartość</th>
          </tr>
        </thead>
        <tbody>
          {average.items.map((item) => (
            <tr key={item.match_id} className={item.excluded ? "excluded" : ""}>
              <td>{fmt.dateShort(item.kickoff)}</td>
              <td>
                {teams[item.opponent_id]?.name ?? item.opponent_id} <span className="venue">({VENUE[item.venue]})</span>
              </td>
              <td>{competitions[item.competition_id]?.name ?? KIND[item.competition_id] ?? item.competition_id}</td>
              <td>
                {item.goals_for_90}:{item.goals_against_90}
                {item.shootout ? " k." : item.extra_time ? " pd." : ""}
              </td>
              <td>
                {fmt.num(item.value)}
                {item.excluded ? <span className="excluded-reason"> — pominięty: {EXCLUDED[item.excluded] ?? item.excluded}</span> : null}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
      <p className="muted small">
        D/W/N — dom, wyjazd, teren neutralny. „pd.” — dogrywka, „k.” — rzuty karne. Wynik podany po 90 minutach z perspektywy drużyny.
      </p>
    </dialog>
  );
}

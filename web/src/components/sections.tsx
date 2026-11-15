import { useState } from "react";
import * as fmt from "../format";
import { ABSENCE_REASON, ABSENCE_STATUS, FLAG, KIND, LINEUP, METRIC, QUALITY, RISK, SOURCE } from "../i18n";
import type { Average, FixtureRef, MatchBundle, TeamPanel } from "../types";
import { FormStrip, Section } from "./common";

export function CompareTable({ bundle, onOpen }: { bundle: MatchBundle; onOpen: (average: Average, teamName: string) => void }) {
  const { home, away } = bundle.match;
  return (
    <table className="compare">
      <thead>
        <tr>
          <th scope="col">{home.short_name}</th>
          <th scope="col" className="metric-col">
            średnio na mecz
          </th>
          <th scope="col">{away.short_name}</th>
        </tr>
      </thead>
      <tbody>
        <tr>
          <td>
            <FormStrip entries={bundle.home.form.entries} teams={bundle.teams} />
          </td>
          <th scope="row" className="metric-col">
            Forma (pkt/mecz)
            <span className="league-ref">
              {fmt.num(bundle.home.form.points_per_game)} – {fmt.num(bundle.away.form.points_per_game)}
            </span>
          </th>
          <td>
            <FormStrip entries={bundle.away.form.entries} teams={bundle.teams} />
          </td>
        </tr>
        {bundle.metrics.map((row) => {
          const label = METRIC[`${row.metric}:${row.perspective}`] ?? row.metric;
          const cell = (average: Average, teamName: string) => (
            <td>
              <button type="button" className="stat-button" onClick={() => onOpen(average, teamName)}>
                <span className="stat-value">{fmt.num(average.value)}</span>
                <span className={`stat-n ${average.n_used < 5 ? "warn" : ""}`}>
                  n={average.n_used}
                  {average.n_used !== average.n_considered ? `/${average.n_considered}` : ""}
                </span>
              </button>
            </td>
          );
          return (
            <tr key={`${row.metric}-${row.perspective}`}>
              {cell(row.home, home.name)}
              <th scope="row" className="metric-col">
                {label}
                {row.league ? <span className="league-ref">liga: {fmt.num(row.league.value)}</span> : null}
              </th>
              {cell(row.away, away.name)}
            </tr>
          );
        })}
      </tbody>
    </table>
  );
}

export function H2HSection({ bundle }: { bundle: MatchBundle }) {
  const [open, setOpen] = useState<string | null>(null);
  const { h2h, teams, competitions } = bundle;
  const last = h2h.last_meeting;
  const name = (id: string) => teams[id]?.name ?? id;
  // Points per game with its sample size; older seasons are often thinly covered.
  const ppg = (summary: TeamPanel["form"] | null) =>
    summary ? `${fmt.num(summary.points_per_game)} (n=${summary.entries.length})` : "—";
  return (
    <Section title="Mecze bezpośrednie" aside={<span className="muted">{h2h.total_meetings} meczów</span>}>
      {last ? (
        <p className="headline">
          Ostatnio <strong>{fmt.date(last.kickoff)}</strong> ({fmt.days(last.days_ago)} temu),{" "}
          {last.neutral_venue ? `teren neutralny: ${last.venue}` : `${last.venue} (${name(last.home_id)})`}:{" "}
          <strong>
            {name(last.home_id)} {fmt.score(last.score)} {name(last.away_id)}
          </strong>
        </p>
      ) : (
        <p className="headline">Te drużyny jeszcze ze sobą nie grały.</p>
      )}
      {h2h.total_meetings ? (
        <p className="muted">
          Bilans po 90 min z perspektywy {bundle.match.home.short_name}: {h2h.a_wins_90} Z, {h2h.draws_90} R, {h2h.b_wins_90} P;
          gole {h2h.a_goals_90}:{h2h.b_goals_90}. Opis historii, nie prognoza — nie uwzględnia siły ani zmian składów.
        </p>
      ) : null}
      {last ? (
        <div className="then-now">
          <span>Forma (pkt/mecz, do 5 meczów):</span>
          <span>
            przed ostatnim H2H {ppg(bundle.home.form_vs_last_h2h.then)} – {ppg(bundle.away.form_vs_last_h2h.then)}
          </span>
          <span>
            teraz {ppg(bundle.home.form_vs_last_h2h.now)} – {ppg(bundle.away.form_vs_last_h2h.now)}
          </span>
        </div>
      ) : null}
      {h2h.coach_changes_since_last.length ? (
        <p className="warn-text">
          Od ostatniego meczu zmienił się trener:{" "}
          {h2h.coach_changes_since_last.map((c) => `${name(c.team_id)} (${c.coach}, od ${fmt.date(c.start)})`).join("; ")}
        </p>
      ) : null}
      <ul className="h2h-list">
        {h2h.meetings.map((meeting) => (
          <li key={meeting.match_id}>
            <button
              type="button"
              className="row-button"
              aria-expanded={open === meeting.match_id}
              onClick={() => setOpen(open === meeting.match_id ? null : meeting.match_id)}
            >
              <span>{fmt.dateShort(meeting.kickoff)}</span>
              <span className="h2h-score">
                {teams[meeting.home_id]?.short_name ?? meeting.home_id} {fmt.score(meeting.score)}{" "}
                {teams[meeting.away_id]?.short_name ?? meeting.away_id}
              </span>
              <span className="muted">{competitions[meeting.competition_id]?.name ?? meeting.competition_id}</span>
            </button>
            {open === meeting.match_id ? (
              <div className="h2h-detail">
                <p>
                  {meeting.neutral_venue ? "Teren neutralny" : "Stadion"}: {meeting.venue}. {fmt.days(meeting.days_ago)} temu.
                </p>
                <p className="muted small">
                  Statystyki tego meczu i forma przed nim pojawią się po podłączeniu zaplecza historii (pakiet „storage”).
                </p>
              </div>
            ) : null}
          </li>
        ))}
      </ul>
    </Section>
  );
}

function Fixture({ fixture, label, bundle }: { fixture: FixtureRef | null; label: string; bundle: MatchBundle }) {
  if (!fixture) return <p className="muted">{label}: brak danych</p>;
  const opponent = bundle.teams[fixture.opponent_id]?.name ?? fixture.opponent_id;
  const competition = bundle.competitions[fixture.competition_id]?.name ?? KIND[fixture.competition_kind] ?? "";
  const where = fixture.venue === "home" ? "dom" : fixture.venue === "away" ? "wyjazd" : "neutralny";
  return (
    <p>
      <span className="muted">{label}:</span> {fmt.kickoff(fixture.kickoff)} — {opponent} ({where}), {competition}
      {fixture.score ? ` — ${fixture.venue === "away" ? fmt.score(fixture.score, true) : fmt.score(fixture.score)}` : ""}
    </p>
  );
}

export function ScheduleSection({ bundle }: { bundle: MatchBundle }) {
  return (
    <Section title="Terminarz i odpoczynek">
      <div className="two-col">
        {[bundle.home, bundle.away].map((panel) => (
          <div key={panel.team.id} className="team-block">
            <h3>{panel.team.name}</h3>
            <Fixture fixture={panel.schedule.previous} label="Poprzedni" bundle={bundle} />
            <Fixture fixture={panel.schedule.next} label="Następny" bundle={bundle} />
            <p>
              Przerwa przed meczem: <strong>{fmt.days(panel.schedule.days_since_previous)}</strong>; do następnego:{" "}
              {fmt.days(panel.schedule.days_to_next)}; meczów w 14 dni: {panel.schedule.matches_last_14_days}
            </p>
            <ul className="chips">
              {panel.schedule.flags.map((flag) => (
                <li key={flag} className="chip chip-warn">
                  {FLAG[flag] ?? flag}
                </li>
              ))}
            </ul>
          </div>
        ))}
      </div>
    </Section>
  );
}

export function AbsenceSection({ bundle }: { bundle: MatchBundle }) {
  return (
    <Section title="Składy, absencje, rotacja">
      <div className="two-col">
        {[bundle.home, bundle.away].map((panel) => (
          <div key={panel.team.id} className="team-block">
            <h3>{panel.team.name}</h3>
            <p>
              Skład: <strong>{LINEUP[panel.lineup_status]}</strong>
              {panel.lineup_updated_at ? <span className="muted"> (stan {fmt.kickoff(panel.lineup_updated_at)})</span> : null}
            </p>
            <p>
              Ryzyko rotacji: <strong>{RISK[panel.rotation_risk]}</strong>{" "}
              <span className="muted">— heurystyka z terminarza, nie wiedza o składzie</span>
            </p>
            {panel.coach ? (
              <p>
                Trener: {panel.coach.coach} <span className="muted">(od {fmt.date(panel.coach.start)}, {fmt.days(panel.coach_days)})</span>
              </p>
            ) : (
              <p className="muted">Trener: brak danych</p>
            )}
            {panel.absences_status === "no_data" ? (
              <p className="warn-text">Brak danych o absencjach — to nie znaczy, że nikt nie wypada.</p>
            ) : panel.absences_status === "none_reported" ? (
              <p>Brak zgłoszonych absencji.</p>
            ) : (
              <ul className="absences">
                {panel.absences.map((absence) => (
                  <li key={absence.player} className={`absence absence-${absence.status}`}>
                    <strong>{absence.player}</strong>
                    {absence.importance === "key" ? <span className="chip">kluczowy</span> : null} — {ABSENCE_REASON[absence.reason]},{" "}
                    {ABSENCE_STATUS[absence.status]}
                    <span className="muted small">
                      {" "}
                      ({SOURCE[absence.source] ?? absence.source}, {fmt.kickoff(absence.updated_at)})
                    </span>
                  </li>
                ))}
              </ul>
            )}
          </div>
        ))}
      </div>
    </Section>
  );
}

export function QualityList({ codes }: { codes: string[] }) {
  if (!codes.length) return null;
  return (
    <Section title="Jakość i kompletność danych">
      <ul className="quality">
        {codes.map((code) => (
          <li key={code}>{QUALITY[code] ?? code}</li>
        ))}
      </ul>
    </Section>
  );
}

import { useEffect, useMemo, useState } from "react";
import { fetchDay } from "../api";
import { DataBanner, ReasonList, Segmented, Status } from "../components/common";
import * as fmt from "../format";
import { navigate } from "../router";
import type { CompetitionRef, DayMatch, DayResponse, TeamRef } from "../types";

type ListName = "watch" | "analysis" | "odds";

const TABS: { value: ListName; label: string }[] = [
  { value: "watch", label: "Do oglądania" },
  { value: "analysis", label: "Do analizy" },
  { value: "odds", label: "Kursy" },
];

export function TodayPage({ search }: { search: string }) {
  const params = new URLSearchParams(search);
  const list = (params.get("lista") as ListName | null) ?? "watch";
  const date = params.get("data");
  const [day, setDay] = useState<DayResponse | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const controller = new AbortController();
    setError(null);
    fetchDay(date, controller.signal)
      .then(setDay)
      .catch((reason: unknown) => {
        if (!controller.signal.aborted) setError(reason instanceof Error ? reason.message : "błąd");
      });
    return () => controller.abort();
  }, [date]);

  const lookups = useMemo(() => {
    const teams: Record<string, TeamRef> = {};
    const competitions: Record<string, CompetitionRef> = {};
    for (const match of day?.matches ?? []) {
      teams[match.home.id] = match.home;
      teams[match.away.id] = match.away;
      competitions[match.competition.id] = match.competition;
    }
    return { teams, competitions };
  }, [day]);

  const setList = (value: ListName) => {
    const next = new URLSearchParams(search);
    next.set("lista", value);
    navigate(`/?${next}`, { replace: true });
  };

  const ordered: DayMatch[] = useMemo(() => {
    if (!day || list === "odds") return [];
    const byId = new Map(day.matches.map((m) => [m.id, m]));
    return day.lists[list].map((id) => byId.get(id)).filter((m): m is DayMatch => Boolean(m));
  }, [day, list]);

  return (
    <main className="page">
      <header className="page-header">
        <h1>Co dziś ciekawego?</h1>
        {day ? <p className="muted">{fmt.date(`${day.date}T12:00:00Z`)} · {day.matches.length} meczów</p> : null}
      </header>
      {day ? <DataBanner data={day.data} /> : null}
      <Segmented label="Lista" value={list} options={TABS} onChange={setList} />
      <Status error={error} loading={!day && !error} />
      {list === "odds" ? (
        <section className="card">
          <h2>Kursy wyłączone</h2>
          <p>
            Ta lista pojawi się dopiero po podłączeniu licencjonowanego źródła kursów, przeglądzie prawnym i walidacji modelu
            prawdopodobieństwa. Do tego czasu aplikacja nie wskazuje „korzystnych kursów”.
          </p>
          <p className="muted small">Status źródła: {day?.lists.odds.status ?? "—"}</p>
        </section>
      ) : (
        <ol className="match-list">
          {ordered.map((match, index) => {
            const interest = match.interest;
            const score = interest[list];
            return (
              <li key={match.id}>
                <button type="button" className="match-card" onClick={() => navigate(`/mecz/${match.id}`)}>
                  <div className="match-card-top">
                    <span className="rank">{index + 1}</span>
                    <span className="muted">
                      {fmt.time(match.kickoff)} · {match.competition.name}
                      {match.round ? ` · ${match.round}` : ""}
                    </span>
                    {interest.discovery ? <span className="chip chip-accent">odkrycie</span> : null}
                    {interest.followed ? <span className="chip">obserwowane</span> : null}
                  </div>
                  <div className="teams">
                    <span>{match.home.name}</span>
                    <span className="vs">–</span>
                    <span>{match.away.name}</span>
                  </div>
                  {score.reasons.length ? (
                    <ReasonList reasons={score.reasons} teams={lookups.teams} competitions={lookups.competitions} limit={3} />
                  ) : (
                    <p className="muted small">Brak wyróżniających sygnałów na tej liście.</p>
                  )}
                  <ReasonList reasons={interest.warnings} teams={lookups.teams} competitions={lookups.competitions} tone="warn" limit={2} />
                </button>
              </li>
            );
          })}
        </ol>
      )}
      <p className="muted small footer-note">
        Kolejność wynika z jawnych reguł; każdy powód jest widoczny. „Do oglądania” uwzględnia Twoje obserwowane drużyny, „Do analizy”
        — tylko okoliczności meczu.
      </p>
    </main>
  );
}

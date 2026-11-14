import { useEffect, useState } from "react";
import { fetchMatch } from "../api";
import { DataBanner, ReasonList, Section, Segmented, Status } from "../components/common";
import { SampleSheet } from "../components/SampleSheet";
import { AbsenceSection, CompareTable, H2HSection, QualityList, ScheduleSection } from "../components/sections";
import * as fmt from "../format";
import { navigate } from "../router";
import type { Average, CompetitionGroup, Filters, MatchBundle, Period, Split } from "../types";

// Filters live in the URL: a link or a reload restores the exact comparison.
function readFilters(search: string): Filters {
  const params = new URLSearchParams(search);
  const size = Number(params.get("okno"));
  return {
    window: [5, 10].includes(size) ? size : 10,
    split: params.get("uklad") === "dom-wyjazd" ? "context" : "all",
    period: params.get("czas") === "z-dogrywka" ? "full" : "regulation",
    competitions: (["league", "cups"] as const).find((value) => params.get("rozgrywki") === value) ?? "all",
  };
}

function writeFilters(pathname: string, filters: Filters): string {
  const params = new URLSearchParams();
  if (filters.window !== 10) params.set("okno", String(filters.window));
  if (filters.split === "context") params.set("uklad", "dom-wyjazd");
  if (filters.period === "full") params.set("czas", "z-dogrywka");
  if (filters.competitions !== "all") params.set("rozgrywki", filters.competitions);
  const query = params.toString();
  return query ? `${pathname}?${query}` : pathname;
}

export function MatchPage({ id, pathname, search }: { id: string; pathname: string; search: string }) {
  const filters = readFilters(search);
  const [bundle, setBundle] = useState<MatchBundle | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [sheet, setSheet] = useState<{ average: Average; teamName: string } | null>(null);
  const key = `${id}|${filters.window}|${filters.split}|${filters.period}|${filters.competitions}`;

  useEffect(() => {
    const controller = new AbortController();
    setError(null);
    fetchMatch(id, filters, controller.signal)
      .then(setBundle)
      .catch((reason: unknown) => {
        if (!controller.signal.aborted) setError(reason instanceof Error ? reason.message : "błąd");
      });
    return () => controller.abort();
    // `key` encodes id and every filter value, so it is the complete dependency.
  }, [key]);

  const update = (patch: Partial<Filters>) => navigate(writeFilters(pathname, { ...filters, ...patch }), { replace: true });

  if (!bundle) {
    return (
      <main className="page">
        <button type="button" className="back" onClick={() => navigate("/")}>
          ← Mecze dnia
        </button>
        <Status error={error} loading={!error} />
      </main>
    );
  }

  const { match } = bundle;
  const insights = [...bundle.interest.analysis.reasons, ...bundle.interest.watch.reasons];
  return (
    <main className="page match-page">
      <button type="button" className="back" onClick={() => navigate("/")}>
        ← Mecze dnia
      </button>
      <header className="match-header">
        <p className="muted">
          {match.competition.name}
          {match.round ? ` · ${match.round}` : ""} · {fmt.kickoff(match.kickoff)}
        </p>
        <h1>
          <span>
            {match.home.name}
            {bundle.home.table_position ? <small> ({bundle.home.table_position}.)</small> : null}
          </span>
          <span className="vs">–</span>
          <span>
            {match.away.name}
            {bundle.away.table_position ? <small> ({bundle.away.table_position}.)</small> : null}
          </span>
        </h1>
        <p className="muted">{match.neutral_venue ? `Teren neutralny: ${match.venue}` : match.venue}</p>
      </header>
      <DataBanner data={bundle.data} />

      <div className="filters" aria-label="Filtry porównania">
        <Segmented<number>
          label="Okno"
          value={filters.window}
          options={[
            { value: 5, label: "5" },
            { value: 10, label: "10" },
          ]}
          onChange={(value) => update({ window: value })}
        />
        <Segmented<Split>
          label="Układ"
          value={filters.split}
          options={[
            { value: "all", label: "Wszystkie" },
            { value: "context", label: "Dom/Wyjazd" },
          ]}
          onChange={(value) => update({ split: value })}
        />
        <Segmented<Period>
          label="Czas"
          value={filters.period}
          options={[
            { value: "regulation", label: "90 min" },
            { value: "full", label: "z dogrywką" },
          ]}
          onChange={(value) => update({ period: value })}
        />
        <Segmented<CompetitionGroup>
          label="Rozgrywki"
          value={filters.competitions}
          options={[
            { value: "all", label: "Wszystkie" },
            { value: "league", label: "Liga" },
            { value: "cups", label: "Puchary" },
          ]}
          onChange={(value) => update({ competitions: value })}
        />
      </div>

      <div className="match-grid">
        <div className="col-main">
          {insights.length || bundle.interest.warnings.length ? (
            <Section title="Najważniejsze">
              <ReasonList reasons={insights} teams={bundle.teams} competitions={bundle.competitions} limit={5} />
              <ReasonList reasons={bundle.interest.warnings} teams={bundle.teams} competitions={bundle.competitions} tone="warn" />
            </Section>
          ) : null}
          <Section
            title="Porównanie"
            aside={
              <span className="muted small">
                {filters.split === "context" ? `${match.home.short_name} u siebie, ${match.away.short_name} na wyjeździe` : "wszystkie mecze"}
              </span>
            }
          >
            <CompareTable bundle={bundle} onOpen={(average, teamName) => setSheet({ average, teamName })} />
            <p className="muted small">Dotknij liczby, aby zobaczyć mecze użyte do średniej. „liga” — średnia drużyny w tej lidze.</p>
          </Section>
          <H2HSection bundle={bundle} />
        </div>
        <div className="col-side">
          <ScheduleSection bundle={bundle} />
          <AbsenceSection bundle={bundle} />
          <QualityList codes={bundle.data_quality} />
        </div>
      </div>

      {sheet ? (
        <SampleSheet
          average={sheet.average}
          teamName={sheet.teamName}
          teams={bundle.teams}
          competitions={bundle.competitions}
          onClose={() => setSheet(null)}
        />
      ) : null}
    </main>
  );
}

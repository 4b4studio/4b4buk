// Mirrors the JSON returned by the backend (see backend/buk/analysis.py).
export type Side = "home" | "away";
export type VenueType = "home" | "away" | "neutral";
export type Split = "all" | "context";
export type Period = "regulation" | "full";
export type CompetitionGroup = "all" | "league" | "cups";

export interface TeamRef { id: string; name: string; short_name: string }
export interface CompetitionRef { id: string; name: string; kind: string }
export interface DataInfo { source: string; label: string; as_of: string; is_demo: boolean }

export interface Reason { code: string; weight: number; params: Record<string, string | number> }
export interface ListScore { score: number; reasons: Reason[] }
export interface Interest {
  match_id: string;
  watch: ListScore;
  analysis: ListScore;
  warnings: Reason[];
  followed: boolean;
  discovery: boolean;
}

export interface DayMatch {
  id: string;
  kickoff: string;
  status: string;
  round: string | null;
  competition: CompetitionRef;
  home: TeamRef;
  away: TeamRef;
  interest: Interest;
}

export interface DayResponse {
  date: string;
  data: DataInfo;
  matches: DayMatch[];
  lists: { watch: string[]; analysis: string[]; odds: { status: string; items: unknown[] } };
}

export interface Score {
  home_90: number; away_90: number;
  home_aet: number | null; away_aet: number | null;
  home_pens: number | null; away_pens: number | null;
}

export interface SampleFilter { window: number; venue: string; competition_kinds: string[]; period: Period }

export interface SampleItem {
  match_id: string;
  kickoff: string;
  competition_id: string;
  opponent_id: string;
  venue: VenueType;
  goals_for_90: number;
  goals_against_90: number;
  extra_time: boolean;
  shootout: boolean;
  value: number | null;
  excluded: string | null;
}

export interface Average {
  team_id: string;
  metric: string;
  perspective: string;
  sample_filter: SampleFilter;
  value: number | null;
  n_used: number;
  n_considered: number;
  items: SampleItem[];
  warnings: string[];
}

export interface LeagueReference { competition_id: string; season: string; value: number | null; n_team_matches: number }
export interface MetricRow { metric: string; perspective: string; home: Average; away: Average; league: LeagueReference | null }

export interface FormEntry {
  match_id: string;
  kickoff: string;
  competition_id: string;
  opponent_id: string;
  venue: VenueType;
  goals_for_90: number;
  goals_against_90: number;
  result_90: "W" | "D" | "L";
  decided_by: "regulation" | "extra_time" | "penalties";
  final_result: "W" | "D" | "L";
}

export interface FormSummary {
  team_id: string;
  entries: FormEntry[];
  wins: number; draws: number; losses: number;
  points_per_game: number | null;
  goals_for: number; goals_against: number;
  warnings: string[];
}

export interface FixtureRef {
  match_id: string;
  kickoff: string;
  competition_id: string;
  competition_kind: string;
  opponent_id: string;
  venue: VenueType;
  status: string;
  score: Score | null;
  extra_time: boolean;
  shootout: boolean;
}

export interface ScheduleContext {
  team_id: string;
  previous: FixtureRef | null;
  next: FixtureRef | null;
  days_since_previous: number | null;
  days_to_next: number | null;
  matches_last_14_days: number;
  flags: string[];
}

export interface Absence {
  team_id: string;
  player: string;
  reason: "injury" | "suspension" | "other";
  status: "confirmed" | "doubtful";
  importance: "key" | "regular" | "unknown";
  source: string;
  updated_at: string;
}

export interface CoachSpell { team_id: string; coach: string; start: string; end: string | null }

export interface TeamPanel {
  team: TeamRef;
  side: Side;
  form: FormSummary;
  form_vs_last_h2h: { then: FormSummary | null; now: FormSummary };
  schedule: ScheduleContext;
  rotation_risk: "low" | "medium" | "high";
  rotation_reasons: string[];
  coach: CoachSpell | null;
  coach_days: number | null;
  absences: Absence[];
  absences_status: "reported" | "none_reported" | "no_data";
  lineup_status: "not_available" | "predicted" | "confirmed";
  lineup_updated_at: string | null;
  table_position: number | null;
}

export interface H2HMeeting {
  match_id: string;
  kickoff: string;
  competition_id: string;
  home_id: string;
  away_id: string;
  venue: string;
  neutral_venue: boolean;
  score: Score;
  days_ago: number;
}

export interface H2HSummary {
  team_a: string;
  team_b: string;
  meetings: H2HMeeting[];
  total_meetings: number;
  a_wins_90: number; draws_90: number; b_wins_90: number;
  a_goals_90: number; b_goals_90: number;
  last_meeting: H2HMeeting | null;
  days_since_last: number | null;
  coach_changes_since_last: { team_id: string; coach: string; start: string }[];
  warnings: string[];
}

export interface MatchBundle {
  match: {
    id: string;
    kickoff: string;
    competition: CompetitionRef;
    round: string | null;
    venue: string;
    neutral_venue: boolean;
    status: string;
    home: TeamRef;
    away: TeamRef;
  };
  split: Split;
  competition_group: CompetitionGroup;
  period: Period;
  window: number;
  home: TeamPanel;
  away: TeamPanel;
  metrics: MetricRow[];
  h2h: H2HSummary;
  interest: Interest;
  data_quality: string[];
  teams: Record<string, TeamRef>;
  competitions: Record<string, CompetitionRef>;
  data: DataInfo;
}

export interface Filters { window: number; split: Split; period: Period; competitions: CompetitionGroup }

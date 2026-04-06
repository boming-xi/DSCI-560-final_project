import type { DoctorProfile } from "@/lib/types";

const scoreLabels: Record<string, string> = {
  specialty_score: "Specialty fit",
  insurance_score: "Insurance fit",
  distance_score: "Distance",
  availability_score: "Availability",
  language_score: "Language",
  trust_score: "Trust",
};

export function RankingExplanation({ doctor }: { doctor: DoctorProfile }) {
  if (!doctor.ranking_breakdown) {
    return null;
  }

  const rows = Object.entries(doctor.ranking_breakdown).filter(([key]) =>
    key.endsWith("_score")
  );

  return (
    <div className="panel explanation-panel">
      <div className="panel-heading">
        <span className="eyebrow">Why this doctor ranks highly</span>
        <h3>{doctor.name}</h3>
        <p>{doctor.ranking_breakdown.summary}</p>
      </div>

      <div className="score-stack">
        {rows.map(([key, value]) => (
          <div className="score-row" key={key}>
            <div className="score-copy">
              <span>{scoreLabels[key]}</span>
              <strong>{Math.round(Number(value) * 100)} / 100</strong>
            </div>
            <div className="score-bar">
              <span style={{ width: `${Math.max(Number(value) * 100, 6)}%` }} />
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}


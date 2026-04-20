import type { DoctorProfile, RankingBreakdown } from "@/lib/types";

const metricRows = [
  { key: "specialty_score", label: "Specialty fit" },
  { key: "insurance_score", label: "Insurance fit" },
  { key: "distance_score", label: "Distance" },
  { key: "availability_score", label: "Availability" },
  { key: "language_score", label: "Language" },
  { key: "trust_score", label: "Trust" },
] as const;

type MetricKey = (typeof metricRows)[number]["key"];

type RankingExplanationProps = {
  doctor?: DoctorProfile;
  doctors?: DoctorProfile[];
};

function getScore(
  breakdown: RankingBreakdown | null | undefined,
  key: MetricKey,
): number {
  return Number(breakdown?.[key] ?? 0);
}

function formatScore(value: number): string {
  return `${Math.round(value * 100)} / 100`;
}

function getTopStrengths(doctor: DoctorProfile): string[] {
  if (!doctor.ranking_breakdown) {
    return [];
  }

  return [...metricRows]
    .sort(
      (left, right) =>
        getScore(doctor.ranking_breakdown, right.key) -
        getScore(doctor.ranking_breakdown, left.key),
    )
    .slice(0, 2)
    .map((item) => item.label);
}

function buildDoctors(props: RankingExplanationProps): DoctorProfile[] {
  if (props.doctors?.length) {
    return props.doctors.filter((doctor) => doctor.ranking_breakdown).slice(0, 3);
  }

  return props.doctor?.ranking_breakdown ? [props.doctor] : [];
}

export function RankingExplanation(props: RankingExplanationProps) {
  const comparisonDoctors = buildDoctors(props);

  if (!comparisonDoctors.length) {
    return null;
  }

  if (comparisonDoctors.length === 1) {
    const doctor = comparisonDoctors[0];

    return (
      <div className="panel explanation-panel">
        <div className="panel-heading">
          <span className="eyebrow">Why this doctor ranks highly</span>
          <h3>{doctor.name}</h3>
          <p>{doctor.ranking_breakdown?.summary}</p>
        </div>

        <div className="ranking-highlight-row">
          {getTopStrengths(doctor).map((strength) => (
            <span className="meta-pill" key={strength}>
              Strong in {strength.toLowerCase()}
            </span>
          ))}
        </div>

        <div className="score-stack">
          {metricRows.map((row) => {
            const value = getScore(doctor.ranking_breakdown, row.key);
            return (
              <div className="score-row" key={row.key}>
                <div className="score-copy">
                  <span>{row.label}</span>
                  <strong>{formatScore(value)}</strong>
                </div>
                <div className="score-bar">
                  <span style={{ width: `${Math.max(value * 100, 6)}%` }} />
                </div>
              </div>
            );
          })}
        </div>
      </div>
    );
  }

  return (
    <section className="panel explanation-panel ranking-comparison-panel">
      <div className="panel-heading">
        <span className="eyebrow">Top 3 doctor comparison</span>
        <h3>Compare the shortlist at a glance</h3>
        <p>
          Instead of one opaque total, this view shows how each top doctor
          performs across specialty fit, insurance confidence, distance,
          availability, language, and trust.
        </p>
      </div>

      <div className="ranking-compare-grid">
        {comparisonDoctors.map((doctor, index) => {
          const strengths = getTopStrengths(doctor);
          return (
            <article
              className={`ranking-compare-card ${index === 0 ? "ranking-compare-card-leading" : ""}`}
              key={doctor.id}
            >
              <div className="ranking-compare-card-top">
                <span className="ranking-rank-badge">#{index + 1}</span>
                {index === 0 ? (
                  <span className="recommended-doctor-tag">Best overall fit</span>
                ) : null}
              </div>
              <h4>{doctor.name}</h4>
              <p className="ranking-compare-subtitle">
                {doctor.specialty} at {doctor.clinic.name}
              </p>
              <div className="badge-row compact-badge-row">
                <span className="badge">{doctor.next_opening_label}</span>
                <span className="badge">{doctor.distance_km} km away</span>
                <span className="badge">
                  {doctor.insurance_verification?.label ?? "Coverage review pending"}
                </span>
              </div>
              <div className="ranking-highlight-row">
                {strengths.map((strength) => (
                  <span className="meta-pill" key={`${doctor.id}-${strength}`}>
                    {strength}
                  </span>
                ))}
              </div>
              <p className="subtle-copy">{doctor.ranking_breakdown?.summary}</p>
            </article>
          );
        })}
      </div>

      <div className="ranking-matrix">
        <div className="ranking-matrix-header ranking-matrix-row">
          <div className="ranking-matrix-label-cell">Decision lens</div>
          {comparisonDoctors.map((doctor) => (
            <div className="ranking-matrix-doctor-cell" key={`header-${doctor.id}`}>
              {doctor.name}
            </div>
          ))}
        </div>

        {metricRows.map((row) => {
          const values = comparisonDoctors.map((doctor) =>
            getScore(doctor.ranking_breakdown, row.key),
          );
          const topValue = Math.max(...values);

          return (
            <div className="ranking-matrix-row" key={row.key}>
              <div className="ranking-matrix-label-cell">{row.label}</div>
              {comparisonDoctors.map((doctor, index) => {
                const value = values[index];
                const isTop = value === topValue;
                return (
                  <div
                    className={`ranking-matrix-score-cell ${isTop ? "ranking-matrix-score-cell-top" : ""}`}
                    key={`${row.key}-${doctor.id}`}
                  >
                    <div className="ranking-matrix-score-copy">
                      <strong>{formatScore(value)}</strong>
                      {isTop ? <span>Best in top 3</span> : null}
                    </div>
                    <div className="ranking-mini-bar">
                      <span style={{ width: `${Math.max(value * 100, 8)}%` }} />
                    </div>
                  </div>
                );
              })}
            </div>
          );
        })}
      </div>
    </section>
  );
}

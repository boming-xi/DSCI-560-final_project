import Link from "next/link";

import { StartDemoLink } from "@/components/StartDemoLink";

const featureCards = [
  {
    title: "Symptom triage",
    body: "Translate free-text symptoms into urgency guidance and a likely care path.",
  },
  {
    title: "Insurance matching",
    body: "Normalize student and newcomer insurance plans into simple copay and referral guidance.",
  },
  {
    title: "Doctor ranking",
    body: "Rank nearby doctors by specialty fit, distance, availability, language, and trust signals.",
  },
  {
    title: "Booking support",
    body: "Turn a recommendation into a scheduled visit with slots and a confirmation flow.",
  },
];

export default function HomePage() {
  return (
    <main className="page-shell">
      <section className="hero panel">
        <div className="hero-copy">
          <span className="eyebrow">DSCI 560 Final Project</span>
          <h1>AI Healthcare Assistant for symptom-to-appointment decision support</h1>
          <p>
            Built for international students and new residents who need help
            figuring out where to go, whether insurance works there, and how to
            book the next step with confidence.
          </p>
          <div className="hero-actions">
            <StartDemoLink />
            <Link className="button button-secondary" href="/chat">
              Open assistant chat
            </Link>
          </div>
        </div>
        <div className="hero-card-grid">
          {featureCards.map((card) => (
            <article className="mini-card" key={card.title}>
              <h3>{card.title}</h3>
              <p>{card.body}</p>
            </article>
          ))}
        </div>
      </section>

      <section className="step-grid">
        <article className="panel">
          <span className="eyebrow">Step 1</span>
          <h2>Symptoms</h2>
          <p>Capture the patient story in natural language.</p>
        </article>
        <article className="panel">
          <span className="eyebrow">Step 2</span>
          <h2>Insurance</h2>
          <p>Match plans, note copays, and surface referral requirements.</p>
        </article>
        <article className="panel">
          <span className="eyebrow">Step 3</span>
          <h2>Recommendations</h2>
          <p>Score doctors with transparent ranking factors.</p>
        </article>
        <article className="panel">
          <span className="eyebrow">Step 4</span>
          <h2>Booking</h2>
          <p>Move from ranked options into a direct booking confirmation.</p>
        </article>
      </section>
    </main>
  );
}

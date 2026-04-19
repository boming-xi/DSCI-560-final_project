import { StartDemoLink } from "@/components/StartDemoLink";

const featureCards = [
  {
    number: "01",
    title: "Symptom Triage",
    body: "Clarify which symptoms need urgent attention and which care setting makes the most sense first.",
  },
  {
    number: "02",
    title: "Insurance Matching",
    body: "Compare marketplace and student coverage with an advisor flow that turns dense plan language into plain decisions.",
  },
  {
    number: "03",
    title: "Doctor Ranking",
    body: "Balance specialty fit, insurance verification, distance, language, and trust signals in one shortlist.",
  },
  {
    number: "04",
    title: "Instant Booking",
    body: "Move from recommendation to a confirmed next step without forcing the user to restart the search journey.",
  },
];

const insuranceMetrics = [
  {
    value: "201",
    label: "plans in advisor coverage",
    tone: "muted",
  },
  {
    value: "12",
    label: "California marketplace carriers",
    tone: "primary",
  },
  {
    value: "5",
    label: "quick-match upload plans",
    tone: "soft",
  },
];

const pathSteps = [
  {
    number: "1",
    title: "Connect",
    body: "Start with symptoms and current needs so the rest of the journey has clinical context.",
  },
  {
    number: "2",
    title: "Analyze",
    body: "Choose existing insurance or let the plan advisor narrow the right coverage path first.",
  },
  {
    number: "3",
    title: "Match",
    body: "Rank doctors using specialty fit, insurance evidence, language, and final-choice guidance.",
  },
  {
    number: "4",
    title: "Book",
    body: "Carry the recommendation into a scheduling step with less uncertainty and less backtracking.",
  },
];

const carrierPills = [
  "Aetna CVS Health",
  "Anthem Blue Cross",
  "Blue Shield of California",
  "Health Net",
  "Kaiser Permanente",
  "L.A. Care",
  "Molina Healthcare",
  "Sharp Health Plan",
];

export default function HomePage() {
  return (
    <main className="page-shell sanctuary-home">
      <section className="sanctuary-hero">
        <div className="sanctuary-hero-copy">
          <span className="eyebrow">The Digital Sanctuary</span>
          <h1>
            Clarity in your
            <span className="headline-accent"> healing journey.</span>
          </h1>
          <p className="sanctuary-lead">
            Navigate symptoms, insurance choice, doctor selection, and booking
            with a calmer interface built for international students and new
            residents who need an authoritative but human guide.
          </p>
          <div className="hero-actions">
            <StartDemoLink label="Begin Guided Care Plan" />
          </div>
          <p className="sanctuary-hero-note">
            Insurance-first care navigation with real marketplace breadth,
            doctor matching, and a final decision room that helps users confirm
            the right clinician before they book.
          </p>
        </div>

        <div className="sanctuary-hero-aside">
          <div className="sanctuary-orb" />
          <article className="assistant-preview-card">
            <div className="assistant-preview-header">
              <div className="assistant-preview-brand">
                <span className="assistant-dot" />
                <div>
                  <strong>Care Guide</strong>
                  <p>Editorial decision support</p>
                </div>
              </div>
              <span className="meta-pill">Live insurance context</span>
            </div>

            <div className="assistant-message assistant-message-system">
              We start by clarifying symptoms, then decide whether insurance
              selection or direct doctor search should come next.
            </div>
            <div className="assistant-message assistant-message-user">
              I need a PPO if possible, I live near USC, and I want a doctor
              who can explain options clearly.
            </div>
            <div className="assistant-preview-summary">
              <span className="eyebrow">Current focus</span>
              <h3>Insurance-aware care navigation</h3>
              <p>
                The system can compare coverage, verify likely in-network
                matches, and carry the chosen plan directly into doctor
                ranking.
              </p>
            </div>
          </article>
        </div>
      </section>

      <section className="sanctuary-section sanctuary-feature-section">
        <div className="sanctuary-section-header">
          <span className="eyebrow">Comprehensive Care Navigation</span>
          <h2>One calm flow from symptoms to the next confirmed care step.</h2>
          <p>
            The experience is organized as a guided editorial journey rather
            than a stack of disconnected forms, so each step informs the one
            that follows.
          </p>
        </div>

        <div className="sanctuary-feature-grid">
          {featureCards.map((card) => (
            <article className="sanctuary-feature-card" key={card.title}>
              <span className="sanctuary-feature-number">{card.number}</span>
              <h3>{card.title}</h3>
              <p>{card.body}</p>
            </article>
          ))}
        </div>
      </section>

      <section className="sanctuary-network-section">
        <span className="eyebrow eyebrow-centered">The Network Advantage</span>
        <h2>Insurance breadth that actually changes the recommendation.</h2>
        <p className="sanctuary-section-copy">
          The insurance layer is not decorative. It changes which plans can be
          chosen, which doctors move up the shortlist, and how confidently a
          user can take the next step.
        </p>

        <div className="sanctuary-metric-row">
          {insuranceMetrics.map((metric) => (
            <article
              className={`sanctuary-metric sanctuary-metric-${metric.tone}`}
              key={metric.label}
            >
              <div className="sanctuary-metric-disc">{metric.value}</div>
              <p>{metric.label}</p>
            </article>
          ))}
        </div>

        <div className="carrier-pill-cloud sanctuary-carrier-cloud">
          {carrierPills.map((carrier) => (
            <span className="meta-pill carrier-pill" key={carrier}>
              {carrier}
            </span>
          ))}
        </div>
      </section>

      <section className="sanctuary-path-section">
        <span className="eyebrow eyebrow-centered">Your Path to Wellness</span>
        <h2>A four-step flow from uncertainty to action.</h2>
        <div className="sanctuary-step-row">
          {pathSteps.map((step) => (
            <article className="sanctuary-step-card" key={step.number}>
              <span className="sanctuary-step-marker" />
              <span className="sanctuary-step-number">{step.number}</span>
              <h3>{step.title}</h3>
              <p>{step.body}</p>
            </article>
          ))}
        </div>
      </section>
    </main>
  );
}

"use client";

import { StartDemoLink } from "@/components/StartDemoLink";
import { useTranslation } from "@/lib/LanguageProvider";

const insuranceMetrics = [
  { value: "201", tone: "muted" },
  { value: "12", tone: "primary" },
  { value: "LA", tone: "soft" },
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
const {t}=useTranslation();

return(
  <main className="page-shell sanctuary-home">

    {/* HERO */}
    <section className="sanctuary-hero">
      <div className="sanctuary-hero-copy">
        <span className="eyebrow">{t.home.sanctuaryLabel}</span>

        <h1>
          {t.home.titleLine1}
          <span className="headline-accent"> {t.home.titleLine2}</span>
        </h1>

        <p className="sanctuary-lead">
          {t.home.subtitle}
        </p>

        <div className="hero-actions">
          <StartDemoLink label={t.home.startButton} />
        </div>

        <p className="sanctuary-hero-note">
          {t.home.heroNote}
        </p>
      </div>

      <div className="sanctuary-hero-aside">
        <div className="sanctuary-orb" />
        <article className="assistant-preview-card">
          <div className="assistant-preview-header">
            <div className="assistant-preview-brand">
              <span className="assistant-dot" />
              <div>
                <strong>{t.home.previewBrand}</strong>
                <p>{t.home.previewSub}</p>
              </div>
            </div>
            <span className="meta-pill">{t.home.previewTag}</span>
          </div>

          <div className="assistant-message assistant-message-system">
            {t.home.previewSystem}
          </div>

          <div className="assistant-message assistant-message-user">
            {t.home.previewUser}
          </div>

          <div className="assistant-preview-summary">
            <span className="eyebrow">{t.home.previewFocus}</span>
            <h3>{t.home.previewTitle}</h3>
            <p>{t.home.previewDescription}</p>
          </div>
        </article>
      </div>
    </section>

    <section className="campus-trust-strip">
      <div className="campus-trust-header">
        <span className="eyebrow">{t.home.trustHeader}</span>
      </div>
      <div className="campus-trust-grid">
        {t.home.trustItems.map((item) => (
          <article className="campus-trust-card" key={item}>
            <span className="campus-trust-marker" />
            <p>{item}</p>
          </article>
        ))}
      </div>
    </section>

    {/* FEATURES */}
    <section className="sanctuary-section sanctuary-feature-section">
      <div className="sanctuary-section-header">
        <span className="eyebrow">{t.home.featureHeader}</span>
        <h2>{t.home.featureTitle}</h2>
        <p>{t.home.featureDescription}</p>
      </div>

      <div className="sanctuary-feature-grid">
        {t.home.featureCards.map((card)=>(
          <article className="sanctuary-feature-card" key={card.number}>
            <span className="sanctuary-feature-number">{card.number}</span>
            <h3>{card.title}</h3>
            <p>{card.body}</p>
          </article>
        ))}
      </div>
    </section>

    {/* NETWORK */}
    <section className="sanctuary-network-section">
      <span className="eyebrow eyebrow-centered">{t.home.networkHeader}</span>
      <h2>{t.home.networkTitle}</h2>

      <div className="sanctuary-metric-row">
        {insuranceMetrics.map((m, index)=>(
          <article
            className={`sanctuary-metric sanctuary-metric-${m.tone}`}
            key={m.value}
          >
            <div className="sanctuary-metric-disc">{m.value}</div>
            <p>{t.home.metrics[index]}</p>
          </article>
        ))}
      </div>

      <div className="carrier-pill-cloud sanctuary-carrier-cloud">
        {carrierPills.map((c)=>(
          <span className="meta-pill carrier-pill" key={c}>
            {c}
          </span>
        ))}
      </div>
    </section>

    {/* PATH */}
    <section className="sanctuary-path-section">
      <span className="eyebrow eyebrow-centered">{t.home.pathHeader}</span>
      <h2>{t.home.pathTitle}</h2>

      <div className="sanctuary-step-row">
        {t.home.pathSteps.map((s)=>(
          <article className="sanctuary-step-card" key={s.number}>
            <span className="sanctuary-step-marker" />
            <span className="sanctuary-step-number">{s.number}</span>
            <h3>{s.title}</h3>
            <p>{s.body}</p>
          </article>
        ))}
      </div>
    </section>

  </main>
);
}

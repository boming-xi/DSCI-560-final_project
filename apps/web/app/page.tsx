"use client";

import { StartDemoLink } from "@/components/StartDemoLink";
import { useTranslation } from "@/lib/LanguageProvider";

type FeatureKey =
  | "feature_1_title" | "feature_1_body"
  | "feature_2_title" | "feature_2_body"
  | "feature_3_title" | "feature_3_body"
  | "feature_4_title" | "feature_4_body";

type StepKey =
  | "step_1_title" | "step_1_body"
  | "step_2_title" | "step_2_body"
  | "step_3_title" | "step_3_body"
  | "step_4_title" | "step_4_body";

type MetricKey =
  | "metric_1"
  | "metric_2"
  | "metric_3";

// ✅ 数据结构改成强类型
const featureCards:{
  number:string;
  titleKey:FeatureKey;
  bodyKey:FeatureKey;
}[]=[
  {number:"01",titleKey:"feature_1_title",bodyKey:"feature_1_body"},
  {number:"02",titleKey:"feature_2_title",bodyKey:"feature_2_body"},
  {number:"03",titleKey:"feature_3_title",bodyKey:"feature_3_body"},
  {number:"04",titleKey:"feature_4_title",bodyKey:"feature_4_body"},
];

const insuranceMetrics:{
  value:string;
  labelKey:MetricKey;
  tone:string;
}[]=[
  {value:"201",labelKey:"metric_1",tone:"muted"},
  {value:"12",labelKey:"metric_2",tone:"primary"},
  {value:"LA",labelKey:"metric_3",tone:"soft"},
];

const pathSteps:{
  number:string;
  titleKey:StepKey;
  bodyKey:StepKey;
}[]=[
  {number:"1",titleKey:"step_1_title",bodyKey:"step_1_body"},
  {number:"2",titleKey:"step_2_title",bodyKey:"step_2_body"},
  {number:"3",titleKey:"step_3_title",bodyKey:"step_3_body"},
  {number:"4",titleKey:"step_4_title",bodyKey:"step_4_body"},
];

const carrierPills=[
  "Aetna CVS Health",
  "Anthem Blue Cross",
  "Blue Shield of California",
  "Health Net",
  "Kaiser Permanente",
  "L.A. Care",
  "Molina Healthcare",
  "Sharp Health Plan",
];

export default function HomePage(){
const {t}=useTranslation();

return(
  <main className="page-shell sanctuary-home">

    {/* HERO */}
    <section className="sanctuary-hero">
      <div className="sanctuary-hero-copy">
        <span className="eyebrow">The Digital Sanctuary</span>

        <h1>
          {t.home_title_1}
          <span className="headline-accent"> {t.home_title_2}</span>
        </h1>

        <p className="sanctuary-lead">
          {t.home_subtitle}
        </p>

        <div className="hero-actions">
          <StartDemoLink label={t.start_button} />
        </div>

        <p className="sanctuary-hero-note">
          {t.hero_note}
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
                <p>{t.preview_sub}</p>
              </div>
            </div>
            <span className="meta-pill">{t.preview_tag}</span>
          </div>

          <div className="assistant-message assistant-message-system">
            {t.preview_sys}
          </div>

          <div className="assistant-message assistant-message-user">
            {t.preview_user}
          </div>

          <div className="assistant-preview-summary">
            <span className="eyebrow">{t.preview_focus}</span>
            <h3>{t.preview_title}</h3>
            <p>{t.preview_desc}</p>
          </div>
        </article>
      </div>
    </section>

    {/* FEATURES */}
    <section className="sanctuary-section sanctuary-feature-section">
      <div className="sanctuary-section-header">
        <span className="eyebrow">{t.feature_header}</span>
        <h2>{t.feature_title}</h2>
        <p>{t.feature_desc}</p>
      </div>

      <div className="sanctuary-feature-grid">
        {featureCards.map((card)=>(
          <article className="sanctuary-feature-card" key={card.number}>
            <span className="sanctuary-feature-number">{card.number}</span>
            <h3>{t[card.titleKey]}</h3>
            <p>{t[card.bodyKey]}</p>
          </article>
        ))}
      </div>
    </section>

    {/* NETWORK */}
    <section className="sanctuary-network-section">
      <span className="eyebrow eyebrow-centered">{t.network_header}</span>
      <h2>{t.network_title}</h2>

      <div className="sanctuary-metric-row">
        {insuranceMetrics.map((m)=>(
          <article
            className={`sanctuary-metric sanctuary-metric-${m.tone}`}
            key={m.value}
          >
            <div className="sanctuary-metric-disc">{m.value}</div>
            <p>{t[m.labelKey]}</p>
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
      <span className="eyebrow eyebrow-centered">{t.path_header}</span>
      <h2>{t.path_title}</h2>

      <div className="sanctuary-step-row">
        {pathSteps.map((s)=>(
          <article className="sanctuary-step-card" key={s.number}>
            <span className="sanctuary-step-marker" />
            <span className="sanctuary-step-number">{s.number}</span>
            <h3>{t[s.titleKey]}</h3>
            <p>{t[s.bodyKey]}</p>
          </article>
        ))}
      </div>
    </section>

  </main>
);
}
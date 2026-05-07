"use client";

import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { AuthStatus } from "@/components/AuthStatus";
import { useTranslation } from "@/lib/LanguageProvider";
import { getLanguageMeta, languageOptions } from "@/lib/i18n";

export default function LayoutContent({
  children,
}:{
  children:React.ReactNode;
}){
  const {t,lang,setLang}=useTranslation();
  const selectedLanguage = getLanguageMeta(lang);
  const pathname = usePathname();
  const router = useRouter();

  const navItems=[
    {href:"/",label:t.layout.nav.overview},
    {href:"/symptom",label:t.layout.nav.symptoms},
    {href:"/insurance",label:t.layout.nav.insurance},
    {href:"/doctors",label:t.layout.nav.doctors},
    {href:"/booking",label:t.layout.nav.booking},
    {href:"/group-chat",label:t.layout.nav.community},
  ];
  const overviewItem = navItems[0];
  const flowItems = navItems.slice(1);
  const currentFlowHref = flowItems.find((item) => item.href === pathname)?.href ?? "";

  return(
    <div className="site-shell">
      <header className="topbar">
        <Link className="brand" href="/">
          <span>{t.layout.brandTitle}</span>
          <small>{t.layout.brandSubtitle}</small>
        </Link>

        <div className="topbar-controls">
          <div className="topbar-navcluster">
            <nav className="topnav">
              <Link
                className={pathname === overviewItem.href ? "is-active" : ""}
                href={overviewItem.href}
              >
                {overviewItem.label}
              </Link>

              <div className="topnav-dropdown">
                <select
                  aria-label={t.layout.nav.flow}
                  className={`topnav-select ${currentFlowHref ? "is-active" : ""}`}
                  onChange={(event) => {
                    if (event.target.value) {
                      router.push(event.target.value);
                    }
                  }}
                  value={currentFlowHref}
                >
                  <option disabled value="">
                    {t.layout.nav.flow}
                  </option>
                  {flowItems.map((item) => (
                    <option key={item.href} value={item.href}>
                      {item.label}
                    </option>
                  ))}
                </select>
              </div>
            </nav>

            <div className="language-switcher">
              <select
                aria-label="Language"
                className="language-switcher-select"
                id="site-language-select"
                onChange={(event) => setLang(event.target.value as typeof lang)}
                title={selectedLanguage.nativeLabel}
                value={lang}
              >
                {languageOptions.map((option) => (
                  <option key={option.value} value={option.value}>
                    {option.nativeLabel}
                  </option>
                ))}
              </select>
            </div>
          </div>

          <AuthStatus />
        </div>
      </header>

      {children}
    </div>
  );
}

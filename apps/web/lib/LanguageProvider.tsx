"use client";

import { createContext, useContext, useEffect, useMemo, useState } from "react";
import {
  detectBrowserLanguage,
  getLanguageMeta,
  getTranslation,
  isSupportedLanguage,
  LANGUAGE_STORAGE_KEY,
  Language,
} from "./i18n";

type ContextType={
  lang:Language;
  setLang:(l:Language)=>void;
  t:ReturnType<typeof getTranslation>;
};

const LanguageContext=createContext<ContextType|null>(null);

export function LanguageProvider({children}:{children:React.ReactNode}){
  const [lang, setLangState] = useState<Language>(() => {
    if (typeof window === "undefined") {
      return "English";
    }
    const saved = window.localStorage.getItem(LANGUAGE_STORAGE_KEY);
    if (isSupportedLanguage(saved)) {
      return saved;
    }
    return detectBrowserLanguage(window.navigator.language);
  });

  const t = useMemo(() => getTranslation(lang), [lang]);

  useEffect(() => {
    if (typeof window === "undefined") {
      return;
    }
    window.localStorage.setItem(LANGUAGE_STORAGE_KEY, lang);
    document.documentElement.lang = getLanguageMeta(lang).htmlLang;
  }, [lang]);

  function setLang(nextLanguage: Language) {
    setLangState(nextLanguage);
  }

  return(
    <LanguageContext.Provider value={{lang,setLang,t}}>
      {children}
    </LanguageContext.Provider>
  );
}

export function useTranslation(){
  const ctx=useContext(LanguageContext);
  if(!ctx) throw new Error("useTranslation must be used inside provider");
  return ctx;
}

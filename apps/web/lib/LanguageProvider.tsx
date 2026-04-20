"use client";

import { createContext,useContext,useState } from "react";
import { Language,getTranslation } from "./i18n";

type ContextType={
  lang:Language;
  setLang:(l:Language)=>void;
  t:ReturnType<typeof getTranslation>;
};

const LanguageContext=createContext<ContextType|null>(null);

export function LanguageProvider({children}:{children:React.ReactNode}){
  const [lang,setLang]=useState<Language>("English");

  const t=getTranslation(lang);

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
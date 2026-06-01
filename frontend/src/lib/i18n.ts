// Configuración de i18next. Una sola fuente de verdad para el idioma: el valor
// inicial sale de las preferencias persistidas (autoai.prefs.v1, vía storage),
// que cae a "es" por DEFAULT_PREFERENCES. Sin autodetección del navegador y sin
// detector/caché propio de i18next: el cambio de idioma lo propaga
// PreferencesContext llamando a i18n.changeLanguage. Ver applyPreferences.ts y
// PreferencesContext.tsx.

import i18n from "i18next";
import { initReactI18next } from "react-i18next";
import { readPreferences } from "./storage";
import es from "../locales/es.json";
import en from "../locales/en.json";

const resources = {
  es: { translation: es },
  en: { translation: en },
} as const;

void i18n.use(initReactI18next).init({
  resources,
  lng: readPreferences().language,
  fallbackLng: "es",
  interpolation: { escapeValue: false },
});

export default i18n;

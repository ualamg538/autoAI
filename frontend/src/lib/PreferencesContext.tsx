// Contexto de preferencias de accesibilidad: centraliza tema, tamaño de fuente
// e idioma, los persiste en localStorage (vía storage.ts) y los aplica al
// <html> (tema + tamaño + lang). El idioma además se propaga a i18next desde
// aquí: este efecto es la única fuente de verdad del cambio de idioma.
//
// El hook `usePreferences` vive en `usePreferences.ts` para no romper el fast
// refresh (este fichero sólo debe exportar componentes; el contexto, al ser una
// constante, sí puede exportarse).

import { useEffect, useState, type ReactNode } from "react";
import {
  readPreferences,
  writePreferences,
  type Preferences,
} from "./storage";
import { applyPreferencesToDocument } from "./applyPreferences";
import i18n from "./i18n";
import {
  PreferencesContext,
  type PreferencesContextValue,
} from "./preferencesContextValue";

export function PreferencesProvider({ children }: { children: ReactNode }) {
  const [prefs, setPrefs] = useState<Preferences>(() => readPreferences());

  // Actualiza un campo en estado y persiste el conjunto completo.
  function update(patch: Partial<Preferences>) {
    setPrefs((prev) => {
      const next = { ...prev, ...patch };
      writePreferences(next);
      return next;
    });
  }

  useEffect(() => {
    applyPreferencesToDocument(prefs);
    void i18n.changeLanguage(prefs.language);
  }, [prefs]);

  const value: PreferencesContextValue = {
    ...prefs,
    setTheme: (theme) => update({ theme }),
    setFontSize: (fontSize) => update({ fontSize }),
    setLanguage: (language) => update({ language }),
  };

  return (
    <PreferencesContext.Provider value={value}>
      {children}
    </PreferencesContext.Provider>
  );
}

// Aplicación de preferencias al documento (tema + tamaño de fuente).
//
// Funciones puras, sin React, para que las pueda usar tanto el
// `PreferencesProvider` (en un `useEffect`) como el script anti-parpadeo de
// `main.tsx`, que corre ANTES de montar React. Así no duplicamos el mapeo.

import type { FontSizePref, LanguagePref, Preferences, ThemePref } from "./storage";

// Tamaño de fuente del <html>. Toda la tipografía está en `rem`, así que
// escalar este valor escala la interfaz proporcionalmente.
const FONT_SIZE_PERCENT: Record<FontSizePref, string> = {
  small: "87.5%",
  normal: "100%",
  large: "112.5%",
};

export function applyTheme(theme: ThemePref): void {
  const html = document.documentElement;
  if (theme === "dark") {
    html.setAttribute("data-theme", "dark");
  } else {
    html.removeAttribute("data-theme");
  }
}

export function applyFontSize(fontSize: FontSizePref): void {
  document.documentElement.style.fontSize = FONT_SIZE_PERCENT[fontSize];
}

export function applyLanguage(language: LanguagePref): void {
  document.documentElement.lang = language;
}

/** Aplica tema, tamaño de fuente e idioma (atributo `lang`) al `<html>`. */
export function applyPreferencesToDocument(prefs: Preferences): void {
  applyTheme(prefs.theme);
  applyFontSize(prefs.fontSize);
  // `lang` del documento. Como esta función la llama tanto main.tsx (antes de
  // React, anti-FOUC) como el useEffect de PreferencesContext, el atributo
  // queda correcto al arrancar y se actualiza al cambiar de idioma. La
  // propagación a i18next la hace PreferencesContext (no aquí, que es puro).
  applyLanguage(prefs.language);
}

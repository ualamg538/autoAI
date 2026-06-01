// Aplicación de preferencias al documento (tema + tamaño de fuente).
//
// Funciones puras, sin React, para que las pueda usar tanto el
// `PreferencesProvider` (en un `useEffect`) como el script anti-parpadeo de
// `main.tsx`, que corre ANTES de montar React. Así no duplicamos el mapeo.

import type { FontSizePref, Preferences, ThemePref } from "./storage";

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

/** Aplica tema y tamaño de fuente al `<html>` de forma síncrona. */
export function applyPreferencesToDocument(prefs: Preferences): void {
  applyTheme(prefs.theme);
  applyFontSize(prefs.fontSize);
  // El idioma no toca el documento todavía: sólo se persiste/expone en el
  // contexto. El bloque de i18n lo consumirá más adelante.
}

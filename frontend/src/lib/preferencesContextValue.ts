// El objeto Context y su tipo, aislados para que tanto el provider
// (PreferencesContext.tsx) como el hook (usePreferences.ts) los importen sin
// que ningún fichero mezcle componentes con otras exportaciones.

import { createContext } from "react";
import type {
  FontSizePref,
  LanguagePref,
  Preferences,
  ThemePref,
} from "./storage";

export interface PreferencesContextValue extends Preferences {
  setTheme: (theme: ThemePref) => void;
  setFontSize: (fontSize: FontSizePref) => void;
  setLanguage: (language: LanguagePref) => void;
}

export const PreferencesContext = createContext<PreferencesContextValue | null>(
  null,
);

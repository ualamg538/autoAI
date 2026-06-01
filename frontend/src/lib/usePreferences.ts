// Hook de acceso a las preferencias. Lanza si se usa fuera del provider.

import { useContext } from "react";
import {
  PreferencesContext,
  type PreferencesContextValue,
} from "./preferencesContextValue";

export function usePreferences(): PreferencesContextValue {
  const ctx = useContext(PreferencesContext);
  if (!ctx) {
    throw new Error("usePreferences debe usarse dentro de <PreferencesProvider>");
  }
  return ctx;
}

// Drawer lateral de ajustes de accesibilidad: tema, tamaño de fuente e idioma.
// Accesible: role="dialog" + aria-modal, foco atrapado, Esc cierra, foco
// inicial al primer control. La devolución del foco al botón disparador la
// gestiona Layout (quien conoce ese botón).

import { useEffect, useRef } from "react";
import { Moon, Sun, X } from "lucide-react";
import { usePreferences } from "../lib/usePreferences";
import type { FontSizePref, LanguagePref } from "../lib/storage";

interface SettingsDrawerProps {
  open: boolean;
  onClose: () => void;
}

const FONT_SIZE_OPTIONS: { value: FontSizePref; label: string }[] = [
  { value: "small", label: "Pequeño" },
  { value: "normal", label: "Normal" },
  { value: "large", label: "Grande" },
];

const LANGUAGE_OPTIONS: { value: LanguagePref; label: string }[] = [
  { value: "es", label: "Español" },
  { value: "en", label: "English" },
];

// Selector de elementos focusables, para atrapar el foco dentro del panel.
const FOCUSABLE =
  'button, [href], input, select, textarea, [tabindex]:not([tabindex="-1"])';

export default function SettingsDrawer({ open, onClose }: SettingsDrawerProps) {
  const { theme, fontSize, language, setTheme, setFontSize, setLanguage } =
    usePreferences();
  const panelRef = useRef<HTMLDivElement>(null);
  const firstControlRef = useRef<HTMLButtonElement>(null);

  // Foco inicial al primer control cuando se abre.
  useEffect(() => {
    if (open) firstControlRef.current?.focus();
  }, [open]);

  // Esc cierra; Tab/Shift+Tab cicla dentro del panel (foco atrapado).
  useEffect(() => {
    if (!open) return;

    function onKeyDown(e: KeyboardEvent) {
      if (e.key === "Escape") {
        e.preventDefault();
        onClose();
        return;
      }
      if (e.key !== "Tab") return;
      const panel = panelRef.current;
      if (!panel) return;
      const focusables = Array.from(
        panel.querySelectorAll<HTMLElement>(FOCUSABLE),
      ).filter((el) => !el.hasAttribute("disabled"));
      if (focusables.length === 0) return;
      const first = focusables[0];
      const last = focusables[focusables.length - 1];
      const active = document.activeElement;
      if (e.shiftKey && active === first) {
        e.preventDefault();
        last.focus();
      } else if (!e.shiftKey && active === last) {
        e.preventDefault();
        first.focus();
      }
    }

    document.addEventListener("keydown", onKeyDown);
    return () => document.removeEventListener("keydown", onKeyDown);
  }, [open, onClose]);

  if (!open) return null;

  const isDark = theme === "dark";

  return (
    <div className="drawer-overlay" onClick={onClose}>
      <div
        className="settings-drawer"
        role="dialog"
        aria-modal="true"
        aria-labelledby="settings-drawer-title"
        ref={panelRef}
        onClick={(e) => e.stopPropagation()}
      >
        <div className="settings-drawer-header">
          <h2 id="settings-drawer-title" className="settings-drawer-title">
            Ajustes
          </h2>
          <button
            type="button"
            className="icon-btn"
            aria-label="Cerrar ajustes"
            onClick={onClose}
          >
            <X size={20} aria-hidden />
          </button>
        </div>

        <div className="settings-drawer-body">
          {/* Tema */}
          <section className="settings-section">
            <h3 className="settings-label">Tema</h3>
            <button
              type="button"
              ref={firstControlRef}
              className="btn-ghost settings-theme-toggle"
              aria-pressed={isDark}
              onClick={() => setTheme(isDark ? "light" : "dark")}
            >
              {isDark ? (
                <Moon size={16} aria-hidden />
              ) : (
                <Sun size={16} aria-hidden />
              )}
              {isDark ? "Oscuro" : "Claro"}
            </button>
          </section>

          {/* Tamaño de fuente */}
          <section className="settings-section">
            <h3 className="settings-label" id="settings-fontsize-label">
              Tamaño de fuente
            </h3>
            <div
              className="settings-radiogroup"
              role="radiogroup"
              aria-labelledby="settings-fontsize-label"
            >
              {FONT_SIZE_OPTIONS.map((opt) => (
                <button
                  key={opt.value}
                  type="button"
                  role="radio"
                  aria-checked={fontSize === opt.value}
                  className={`settings-radio${
                    fontSize === opt.value ? " selected" : ""
                  }`}
                  onClick={() => setFontSize(opt.value)}
                >
                  {opt.label}
                </button>
              ))}
            </div>
          </section>

          {/* Idioma */}
          <section className="settings-section">
            <h3 className="settings-label" id="settings-language-label">
              Idioma
            </h3>
            <div
              className="settings-radiogroup"
              role="radiogroup"
              aria-labelledby="settings-language-label"
            >
              {LANGUAGE_OPTIONS.map((opt) => (
                <button
                  key={opt.value}
                  type="button"
                  role="radio"
                  aria-checked={language === opt.value}
                  className={`settings-radio${
                    language === opt.value ? " selected" : ""
                  }`}
                  onClick={() => setLanguage(opt.value)}
                >
                  {opt.label}
                </button>
              ))}
            </div>
          </section>
        </div>
      </div>
    </div>
  );
}

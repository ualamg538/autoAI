import { useRef, useState, type ReactNode } from "react";
import { Car, Menu, Settings } from "lucide-react";
import Sidebar, { type ViewKey } from "./Sidebar";
import SettingsDrawer from "./SettingsDrawer";

interface LayoutProps {
  activeView: ViewKey;
  onSelectView: (view: ViewKey) => void;
  children: ReactNode;
}

export default function Layout({
  activeView,
  onSelectView,
  children,
}: LayoutProps) {
  const [collapsed, setCollapsed] = useState(false);
  const [settingsOpen, setSettingsOpen] = useState(false);
  const settingsBtnRef = useRef<HTMLButtonElement>(null);

  function closeSettings() {
    setSettingsOpen(false);
    // Devuelve el foco al botón que abrió el drawer (accesibilidad).
    settingsBtnRef.current?.focus();
  }

  return (
    <div className="app-root">
      <header className="topbar">
        <div className="topbar-left">
          <button
            type="button"
            className="icon-btn"
            aria-label={collapsed ? "Expandir menú" : "Colapsar menú"}
            onClick={() => setCollapsed((c) => !c)}
          >
            <Menu size={20} aria-hidden />
          </button>
        </div>
        <div className="topbar-center">
          <Car className="topbar-brand-icon" size={20} aria-hidden />
          <span>AutoAI</span>
        </div>
        <div className="topbar-right">
          <button
            type="button"
            className="icon-btn"
            aria-label="Ajustes"
            ref={settingsBtnRef}
            aria-haspopup="dialog"
            aria-expanded={settingsOpen}
            onClick={() => setSettingsOpen(true)}
          >
            <Settings size={20} aria-hidden />
          </button>
        </div>
      </header>
      <div className="app-body">
        <Sidebar
          collapsed={collapsed}
          activeView={activeView}
          onSelectView={onSelectView}
        />
        <main className="content">{children}</main>
      </div>
      <SettingsDrawer open={settingsOpen} onClose={closeSettings} />
    </div>
  );
}

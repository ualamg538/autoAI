import { useState, type ReactNode } from "react";
import Sidebar, { type ViewKey } from "./Sidebar";

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
            ☰
          </button>
        </div>
        <div className="topbar-center">
          <span aria-hidden>🚗</span>
          <span>AutoAI</span>
        </div>
        <div className="topbar-right">
          <button type="button" className="icon-btn" aria-label="Ajustes">
            ⚙️
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
    </div>
  );
}

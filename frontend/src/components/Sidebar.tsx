export type ViewKey = "assistant" | "catalog" | "history" | "favorites";

interface SidebarItem {
  key: ViewKey;
  label: string;
  icon: string;
}

const ITEMS: SidebarItem[] = [
  { key: "assistant", label: "Asistente", icon: "💬" },
  { key: "catalog", label: "Catálogo", icon: "📖" },
  { key: "history", label: "Historial", icon: "🕐" },
  { key: "favorites", label: "Favoritos", icon: "🤍" },
];

interface SidebarProps {
  collapsed: boolean;
  activeView: ViewKey;
  onSelectView: (view: ViewKey) => void;
}

export default function Sidebar({
  collapsed,
  activeView,
  onSelectView,
}: SidebarProps) {
  return (
    <nav
      className={`sidebar${collapsed ? " collapsed" : ""}`}
      aria-label="Navegación principal"
    >
      {ITEMS.map((item) => (
        <button
          key={item.key}
          type="button"
          className={`sidebar-item${activeView === item.key ? " active" : ""}`}
          onClick={() => onSelectView(item.key)}
          title={collapsed ? item.label : undefined}
        >
          <span className="sidebar-item-icon" aria-hidden>
            {item.icon}
          </span>
          <span className="sidebar-item-label">{item.label}</span>
        </button>
      ))}
    </nav>
  );
}

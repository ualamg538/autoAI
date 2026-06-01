import {
  BookOpen,
  Clock,
  Heart,
  MessageSquare,
  type LucideIcon,
} from "lucide-react";

export type ViewKey = "assistant" | "catalog" | "history" | "favorites";

interface SidebarItem {
  key: ViewKey;
  label: string;
  icon: LucideIcon;
}

const ITEMS: SidebarItem[] = [
  { key: "assistant", label: "Asistente", icon: MessageSquare },
  { key: "catalog", label: "Catálogo", icon: BookOpen },
  { key: "history", label: "Historial", icon: Clock },
  { key: "favorites", label: "Favoritos", icon: Heart },
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
      {ITEMS.map((item) => {
        const Icon = item.icon;
        return (
          <button
            key={item.key}
            type="button"
            className={`sidebar-item${activeView === item.key ? " active" : ""}`}
            onClick={() => onSelectView(item.key)}
            title={collapsed ? item.label : undefined}
          >
            <span className="sidebar-item-icon" aria-hidden>
              <Icon size={16} />
            </span>
            <span className="sidebar-item-label">{item.label}</span>
          </button>
        );
      })}
    </nav>
  );
}

import {
  BookOpen,
  Clock,
  Heart,
  MessageSquare,
  type LucideIcon,
} from "lucide-react";
import { useTranslation } from "react-i18next";

export type ViewKey = "assistant" | "catalog" | "history" | "favorites";

interface SidebarItem {
  key: ViewKey;
  labelKey: string;
  icon: LucideIcon;
}

const ITEMS: SidebarItem[] = [
  { key: "assistant", labelKey: "sidebar.assistant", icon: MessageSquare },
  { key: "catalog", labelKey: "sidebar.catalog", icon: BookOpen },
  { key: "history", labelKey: "sidebar.history", icon: Clock },
  { key: "favorites", labelKey: "sidebar.favorites", icon: Heart },
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
  const { t } = useTranslation();
  return (
    <nav
      className={`sidebar${collapsed ? " collapsed" : ""}`}
      aria-label={t("sidebar.nav")}
    >
      {ITEMS.map((item) => {
        const Icon = item.icon;
        const label = t(item.labelKey);
        return (
          <button
            key={item.key}
            type="button"
            className={`sidebar-item${activeView === item.key ? " active" : ""}`}
            onClick={() => onSelectView(item.key)}
            title={collapsed ? label : undefined}
          >
            <span className="sidebar-item-icon" aria-hidden>
              <Icon size={16} />
            </span>
            <span className="sidebar-item-label">{label}</span>
          </button>
        );
      })}
    </nav>
  );
}

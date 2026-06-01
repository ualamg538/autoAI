import { useState } from "react";
import { MessageSquareDashed, Trash2 } from "lucide-react";
import { useTranslation } from "react-i18next";
import {
  deleteSession,
  listSessions,
  type ChatSession,
} from "../lib/storage";

const fmt = new Intl.DateTimeFormat("es-ES", {
  dateStyle: "medium",
  timeStyle: "short",
});

export default function History({
  onOpenSession,
}: {
  onOpenSession: (id: string) => void;
}) {
  const { t } = useTranslation();
  const [sessions, setSessions] = useState<ChatSession[]>(() =>
    listSessions(),
  );

  function remove(id: string) {
    deleteSession(id);
    setSessions(listSessions());
  }

  if (sessions.length === 0) {
    return (
      <div className="aux-view">
        <div className="state-block state-empty">
          <span className="state-icon">
            <MessageSquareDashed size={24} aria-hidden />
          </span>
          <p className="state-text">{t("history.empty")}</p>
        </div>
      </div>
    );
  }

  return (
    <div className="aux-view">
      <h2 className="aux-title">{t("history.title")}</h2>
      <ul className="history-list">
        {sessions.map((s) => (
          <li key={s.id} className="history-item">
            <button
              type="button"
              className="history-open"
              onClick={() => onOpenSession(s.id)}
            >
              <span className="history-item-title">{s.title}</span>
              <span className="history-item-meta">
                {fmt.format(new Date(s.updatedAt))} · {s.messages.length}{" "}
                {t("history.messages")}
              </span>
            </button>
            <button
              type="button"
              className="history-delete"
              aria-label={t("history.delete")}
              title={t("history.delete")}
              onClick={() => remove(s.id)}
            >
              <Trash2 size={16} aria-hidden />
            </button>
          </li>
        ))}
      </ul>
    </div>
  );
}

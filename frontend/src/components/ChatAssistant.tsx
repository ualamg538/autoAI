import {
  useEffect,
  useRef,
  useState,
  type FormEvent,
  type KeyboardEvent,
} from "react";
import { ArrowUp, Plus } from "lucide-react";
import { useTranslation } from "react-i18next";
import MessageBubble from "./MessageBubble";
import {
  sendChat,
  type ChatMessage,
  type ChatResponse,
} from "../lib/api";
import {
  getSession,
  saveSession,
  setCurrentSessionId,
  type UiMessage,
} from "../lib/storage";
import { usePreferences } from "../lib/usePreferences";

function uiMessagesToHistory(uiMessages: UiMessage[]): ChatMessage[] {
  return uiMessages.map((m) =>
    m.role === "user"
      ? { role: "user", content: m.content }
      : {
          role: "assistant",
          content: JSON.stringify({ blocks: m.blocks } satisfies ChatResponse),
        },
  );
}

interface ChatAssistantProps {
  /** Sesión activa. El componente se remonta (key) al cambiar. */
  sessionId: string;
  /** Inicia una conversación nueva (App genera otra sesión). */
  onNewSession: () => void;
}

export default function ChatAssistant({
  sessionId,
  onNewSession,
}: ChatAssistantProps) {
  const { t } = useTranslation();
  const { language } = usePreferences();
  const [messages, setMessages] = useState<UiMessage[]>(
    () => getSession(sessionId)?.messages ?? [],
  );
  const [draft, setDraft] = useState("");
  const [loading, setLoading] = useState(false);
  const streamEndRef = useRef<HTMLDivElement | null>(null);
  const nextIdRef = useRef(
    messages.reduce((max, m) => Math.max(max, m.id), 0) + 1,
  );

  useEffect(() => {
    streamEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, loading]);

  // Persiste la conversación y la marca como la sesión activa.
  useEffect(() => {
    if (messages.length === 0) return;
    saveSession(sessionId, messages);
    setCurrentSessionId(sessionId);
  }, [sessionId, messages]);

  async function submit(text: string) {
    const trimmed = text.trim();
    if (!trimmed || loading) return;

    const userMsg: UiMessage = {
      id: nextIdRef.current++,
      role: "user",
      content: trimmed,
    };
    const nextMessages = [...messages, userMsg];
    setMessages(nextMessages);
    setDraft("");
    setLoading(true);

    try {
      const history = uiMessagesToHistory(nextMessages);
      const reply = await sendChat(history, language);
      setMessages((prev) => [
        ...prev,
        {
          id: nextIdRef.current++,
          role: "assistant",
          blocks: reply.blocks,
        },
      ]);
    } catch {
      setMessages((prev) => [
        ...prev,
        {
          id: nextIdRef.current++,
          role: "assistant",
          blocks: [
            {
              type: "text",
              content: t("chat.error"),
            },
          ],
          isError: true,
        },
      ]);
    } finally {
      setLoading(false);
    }
  }

  function handleHeroSubmit(e: FormEvent) {
    e.preventDefault();
    submit(draft);
  }

  function handleInputKeyDown(e: KeyboardEvent<HTMLTextAreaElement>) {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      submit(draft);
    }
  }

  if (messages.length === 0) {
    return (
      <div className="chat-hero">
        <h1 className="chat-hero-title">
          {t("chat.heroTitleLine1")}
          <br />
          {t("chat.heroTitleLine2")}
        </h1>
        <form className="chat-hero-form" onSubmit={handleHeroSubmit}>
          <textarea
            className="chat-hero-textarea"
            placeholder={t("chat.heroPlaceholder")}
            value={draft}
            onChange={(e) => setDraft(e.target.value)}
            onKeyDown={handleInputKeyDown}
            disabled={loading}
            autoFocus
          />
          <button
            type="submit"
            className="btn-primary"
            disabled={loading || !draft.trim()}
          >
            {t("chat.getAnswer")}
          </button>
        </form>
        <p className="chat-disclaimer">{t("chat.disclaimer")}</p>
      </div>
    );
  }

  return (
    <div className="chat-conversation">
      <div className="chat-toolbar">
        <button
          type="button"
          className="btn-ghost"
          onClick={onNewSession}
          disabled={loading}
        >
          <Plus size={16} aria-hidden />
          {t("chat.newConversation")}
        </button>
      </div>
      <div className="chat-stream">
        <div className="chat-stream-inner">
          {messages.map((m) =>
            m.role === "user" ? (
              <MessageBubble
                key={m.id}
                role="user"
                content={m.content}
                isError={m.isError}
              />
            ) : (
              <MessageBubble
                key={m.id}
                role="assistant"
                blocks={m.blocks}
                isError={m.isError}
              />
            ),
          )}
          {loading ? (
            <div className="msg ai">
              <div className="msg-content">
                <span className="typing-dots" aria-label={t("chat.typing")}>
                  <span />
                  <span />
                  <span />
                </span>
              </div>
            </div>
          ) : null}
          <div ref={streamEndRef} />
        </div>
      </div>
      <div className="chat-input-bar">
        <form
          className="chat-input-pill"
          onSubmit={(e) => {
            e.preventDefault();
            submit(draft);
          }}
        >
          <textarea
            className="chat-input-textarea"
            placeholder={t("chat.inputPlaceholder")}
            value={draft}
            onChange={(e) => setDraft(e.target.value)}
            onKeyDown={handleInputKeyDown}
            rows={1}
            disabled={loading}
          />
          <button
            type="submit"
            className="send-btn"
            aria-label={t("chat.send")}
            disabled={loading || !draft.trim()}
          >
            <ArrowUp size={18} aria-hidden />
          </button>
        </form>
        <p className="chat-disclaimer">{t("chat.disclaimer")}</p>
      </div>
    </div>
  );
}

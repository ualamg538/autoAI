import {
  useEffect,
  useRef,
  useState,
  type FormEvent,
  type KeyboardEvent,
} from "react";
import MessageBubble from "./MessageBubble";
import { sendChat, type ChatMessage } from "../lib/api";

interface UiMessage extends ChatMessage {
  id: number;
  isError?: boolean;
}

export default function ChatAssistant() {
  const [messages, setMessages] = useState<UiMessage[]>([]);
  const [draft, setDraft] = useState("");
  const [loading, setLoading] = useState(false);
  const streamEndRef = useRef<HTMLDivElement | null>(null);
  const nextIdRef = useRef(1);

  useEffect(() => {
    streamEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, loading]);

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
      const history: ChatMessage[] = nextMessages.map(({ role, content }) => ({
        role,
        content,
      }));
      const reply = await sendChat(history);
      setMessages((prev) => [
        ...prev,
        {
          id: nextIdRef.current++,
          role: "assistant",
          content: reply,
        },
      ]);
    } catch {
      setMessages((prev) => [
        ...prev,
        {
          id: nextIdRef.current++,
          role: "assistant",
          content: "Error al conectar con el asistente. Inténtalo de nuevo.",
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
          Pregunta lo que quieras
          <br />
          sobre tu próximo coche
        </h1>
        <form className="chat-hero-form" onSubmit={handleHeroSubmit}>
          <textarea
            className="chat-hero-textarea"
            placeholder="Recomienda el mejor coche para un estudiante..."
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
            Obtener respuesta
          </button>
        </form>
      </div>
    );
  }

  return (
    <div className="chat-conversation">
      <div className="chat-stream">
        <div className="chat-stream-inner">
          {messages.map((m) => (
            <MessageBubble
              key={m.id}
              role={m.role}
              content={m.content}
              isError={m.isError}
            />
          ))}
          {loading ? (
            <div className="msg ai">
              <div className="msg-content">
                <span className="typing-dots" aria-label="Escribiendo">
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
            placeholder="Escribe un mensaje..."
            value={draft}
            onChange={(e) => setDraft(e.target.value)}
            onKeyDown={handleInputKeyDown}
            rows={1}
            disabled={loading}
          />
          <button
            type="submit"
            className="send-btn"
            aria-label="Enviar"
            disabled={loading || !draft.trim()}
          >
            ↑
          </button>
        </form>
      </div>
    </div>
  );
}

import {
  useEffect,
  useRef,
  useState,
  type FormEvent,
  type KeyboardEvent,
} from "react";
import MessageBubble from "./MessageBubble";
import {
  sendChat,
  type Block,
  type ChatMessage,
  type ChatResponse,
} from "../lib/api";

type UiMessage =
  | { id: number; role: "user"; content: string; isError?: boolean }
  | { id: number; role: "assistant"; blocks: Block[]; isError?: boolean };

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
      const history = uiMessagesToHistory(nextMessages);
      const reply = await sendChat(history);
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
              content: "Error al conectar con el asistente. Inténtalo de nuevo.",
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

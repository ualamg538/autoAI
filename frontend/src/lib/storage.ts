// Persistencia en localStorage para Favoritos e Historial de chat (Fase 5).
// No hay backend de usuarios en el TFG: todo vive en el navegador.

import { useSyncExternalStore } from "react";
import type { Block } from "./api";

const FAVORITES_KEY = "autoai.favorites.v1";
const SESSIONS_KEY = "autoai.chat.sessions.v1";
const CURRENT_SESSION_KEY = "autoai.chat.current.v1";

/* ---------- Favoritos (lista de IDs de coche) ---------- */

const favoriteListeners = new Set<() => void>();
const EMPTY_FAVORITES: number[] = [];

// `useSyncExternalStore` exige que getSnapshot devuelva una referencia
// estable mientras los datos no cambien, o provocaría un bucle de renders.
let favoritesCache: number[] | null = null;

function readFavorites(): number[] {
  try {
    const raw = localStorage.getItem(FAVORITES_KEY);
    if (!raw) return [];
    const parsed = JSON.parse(raw) as unknown;
    if (!Array.isArray(parsed)) return [];
    return parsed.filter((x): x is number => typeof x === "number");
  } catch {
    return [];
  }
}

function favoritesSnapshot(): number[] {
  if (favoritesCache === null) favoritesCache = readFavorites();
  return favoritesCache;
}

function invalidateAndNotify(): void {
  favoritesCache = null;
  favoriteListeners.forEach((l) => l());
}

function writeFavorites(ids: number[]): void {
  localStorage.setItem(FAVORITES_KEY, JSON.stringify(ids));
  invalidateAndNotify();
}

export function getFavorites(): number[] {
  return favoritesSnapshot();
}

export function isFavorite(id: number): boolean {
  return favoritesSnapshot().includes(id);
}

export function toggleFavorite(id: number): void {
  const ids = readFavorites();
  const next = ids.includes(id)
    ? ids.filter((x) => x !== id)
    : [...ids, id];
  writeFavorites(next);
}

function subscribeFavorites(listener: () => void): () => void {
  favoriteListeners.add(listener);
  // Sincroniza entre pestañas / ventanas.
  const onStorage = (e: StorageEvent) => {
    if (e.key === FAVORITES_KEY) invalidateAndNotify();
  };
  window.addEventListener("storage", onStorage);
  return () => {
    favoriteListeners.delete(listener);
    window.removeEventListener("storage", onStorage);
  };
}

/**
 * Hook reactivo: devuelve la lista actual de IDs favoritos y se re-renderiza
 * cuando cambia (en esta pestaña o en otra).
 */
export function useFavorites(): number[] {
  return useSyncExternalStore(
    subscribeFavorites,
    favoritesSnapshot,
    () => EMPTY_FAVORITES,
  );
}

/* ---------- Historial de chat (sesiones de conversación) ---------- */

export type UiMessage =
  | { id: number; role: "user"; content: string; isError?: boolean }
  | { id: number; role: "assistant"; blocks: Block[]; isError?: boolean };

export interface ChatSession {
  id: string;
  title: string;
  createdAt: number;
  updatedAt: number;
  messages: UiMessage[];
}

export function newSessionId(): string {
  return `s_${Date.now()}_${Math.random().toString(36).slice(2, 8)}`;
}

function isChatSession(value: unknown): value is ChatSession {
  if (!value || typeof value !== "object") return false;
  const s = value as Record<string, unknown>;
  return (
    typeof s.id === "string" &&
    typeof s.title === "string" &&
    Array.isArray(s.messages)
  );
}

function readSessions(): Record<string, ChatSession> {
  try {
    const raw = localStorage.getItem(SESSIONS_KEY);
    if (!raw) return {};
    const parsed = JSON.parse(raw) as unknown;
    if (!parsed || typeof parsed !== "object") return {};
    // Filtra entradas con forma inválida (en línea con readFavorites).
    const out: Record<string, ChatSession> = {};
    for (const [key, value] of Object.entries(parsed as Record<string, unknown>)) {
      if (isChatSession(value)) out[key] = value;
    }
    return out;
  } catch {
    return {};
  }
}

function writeSessions(sessions: Record<string, ChatSession>): void {
  localStorage.setItem(SESSIONS_KEY, JSON.stringify(sessions));
}

/** Sesiones ordenadas de más reciente a más antigua. */
export function listSessions(): ChatSession[] {
  return Object.values(readSessions()).sort(
    (a, b) => b.updatedAt - a.updatedAt,
  );
}

export function getSession(id: string): ChatSession | null {
  return readSessions()[id] ?? null;
}

function deriveTitle(messages: UiMessage[]): string {
  const firstUser = messages.find((m) => m.role === "user");
  if (firstUser && firstUser.role === "user") {
    const t = firstUser.content.trim().replace(/\s+/g, " ");
    return t.length > 60 ? `${t.slice(0, 60)}…` : t || "Conversación";
  }
  return "Conversación";
}

/** Inserta o actualiza una sesión. No persiste conversaciones vacías. */
export function saveSession(id: string, messages: UiMessage[]): void {
  if (messages.length === 0) return;
  const sessions = readSessions();
  const now = Date.now();
  const prev = sessions[id];
  sessions[id] = {
    id,
    title: deriveTitle(messages),
    createdAt: prev?.createdAt ?? now,
    updatedAt: now,
    messages,
  };
  writeSessions(sessions);
}

export function deleteSession(id: string): void {
  const sessions = readSessions();
  if (id in sessions) {
    delete sessions[id];
    writeSessions(sessions);
  }
  if (getCurrentSessionId() === id) {
    localStorage.removeItem(CURRENT_SESSION_KEY);
  }
}

export function getCurrentSessionId(): string | null {
  return localStorage.getItem(CURRENT_SESSION_KEY);
}

export function setCurrentSessionId(id: string): void {
  localStorage.setItem(CURRENT_SESSION_KEY, id);
}

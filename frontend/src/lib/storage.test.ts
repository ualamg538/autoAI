import { beforeEach, describe, expect, it, vi } from "vitest";
import type { UiMessage } from "./storage";

// Claves internas de storage.ts (no exportadas). Las replicamos para sembrar
// datos directamente en localStorage en los tests de "forma inesperada".
const FAVORITES_KEY = "autoai.favorites.v1";
const SESSIONS_KEY = "autoai.chat.sessions.v1";
const CURRENT_SESSION_KEY = "autoai.chat.current.v1";

// storage.ts cachea los favoritos en estado de módulo (favoritesCache) porque
// useSyncExternalStore exige snapshots estables. Para que cada test parta de un
// cache limpio reimportamos el módulo tras vi.resetModules(); así getFavorites()
// vuelve a leer de localStorage en lugar de devolver un cache obsoleto.
async function freshStorage() {
  vi.resetModules();
  return await import("./storage");
}

function userMsg(id: number, content: string): UiMessage {
  return { id, role: "user", content };
}

beforeEach(() => {
  localStorage.clear();
});

/* ---------- Favoritos ---------- */

describe("favoritos: lectura con datos corruptos", () => {
  it("devuelve [] con JSON inválido", async () => {
    localStorage.setItem(FAVORITES_KEY, "{no es json");
    const { getFavorites } = await freshStorage();
    expect(getFavorites()).toEqual([]);
  });

  it("devuelve [] si el valor no es un array", async () => {
    localStorage.setItem(FAVORITES_KEY, JSON.stringify({ a: 1 }));
    const { getFavorites } = await freshStorage();
    expect(getFavorites()).toEqual([]);
  });

  it("filtra los elementos que no son número", async () => {
    localStorage.setItem(
      FAVORITES_KEY,
      JSON.stringify([1, "2", null, 3, { x: 1 }]),
    );
    const { getFavorites } = await freshStorage();
    expect(getFavorites()).toEqual([1, 3]);
  });
});

describe("favoritos: toggle / isFavorite", () => {
  it("añade y quita un id", async () => {
    const { toggleFavorite, isFavorite, getFavorites } = await freshStorage();
    expect(isFavorite(7)).toBe(false);

    toggleFavorite(7);
    expect(isFavorite(7)).toBe(true);
    expect(getFavorites()).toEqual([7]);

    toggleFavorite(7);
    expect(isFavorite(7)).toBe(false);
    expect(getFavorites()).toEqual([]);
  });

  it("mantiene varios favoritos", async () => {
    const { toggleFavorite, getFavorites } = await freshStorage();
    toggleFavorite(1);
    toggleFavorite(2);
    expect(getFavorites()).toEqual([1, 2]);
  });
});

/* ---------- Sesiones de chat ---------- */

describe("sesiones: lectura con forma inesperada", () => {
  it("listSessions() devuelve [] con JSON inválido (sin lanzar)", async () => {
    localStorage.setItem(SESSIONS_KEY, "{no es json");
    const { listSessions } = await freshStorage();
    expect(() => listSessions()).not.toThrow();
    expect(listSessions()).toEqual([]);
  });

  it("listSessions() devuelve [] si el valor es un array, no un objeto", async () => {
    // Un array pasa el typeof === "object"; Object.entries lo recorre por índice
    // y ninguna entrada cumple isChatSession, así que el resultado es vacío.
    localStorage.setItem(SESSIONS_KEY, JSON.stringify([1, 2, 3]));
    const { listSessions } = await freshStorage();
    expect(listSessions()).toEqual([]);
  });

  it("descarta entradas que no cumplen isChatSession", async () => {
    const corrupto = {
      sinMessages: { id: "a", title: "t", createdAt: 1, updatedAt: 1 },
      idNumerico: { id: 5, title: "t", messages: [], createdAt: 1, updatedAt: 1 },
      buena: {
        id: "ok",
        title: "Buena",
        createdAt: 1,
        updatedAt: 1,
        messages: [],
      },
    };
    localStorage.setItem(SESSIONS_KEY, JSON.stringify(corrupto));
    const { listSessions, getSession } = await freshStorage();
    const sesiones = listSessions();
    expect(sesiones).toHaveLength(1);
    expect(sesiones[0].id).toBe("ok");
    expect(getSession("sinMessages")).toBeNull();
    expect(getSession("idNumerico")).toBeNull();
  });

  it("getSession() de un id inexistente devuelve null", async () => {
    const { getSession } = await freshStorage();
    expect(getSession("nope")).toBeNull();
  });
});

describe("sesiones: guardar / listar / borrar", () => {
  it("saveSession ignora conversaciones vacías", async () => {
    const { saveSession, listSessions } = await freshStorage();
    saveSession("s1", []);
    expect(listSessions()).toEqual([]);
  });

  it("listSessions ordena por updatedAt descendente", async () => {
    const { saveSession, listSessions } = await freshStorage();
    // Dos guardados separados en el tiempo: el segundo debe quedar primero.
    const t0 = 1_000;
    const t1 = 2_000;
    const spy = vi.spyOn(Date, "now");
    spy.mockReturnValue(t0);
    saveSession("vieja", [userMsg(1, "primera")]);
    spy.mockReturnValue(t1);
    saveSession("nueva", [userMsg(2, "segunda")]);
    spy.mockRestore();

    const ids = listSessions().map((s) => s.id);
    expect(ids).toEqual(["nueva", "vieja"]);
  });

  it("deriva el título recortando a 60 caracteres con elipsis", async () => {
    const { saveSession, getSession } = await freshStorage();
    const largo = "a".repeat(80);
    saveSession("s1", [userMsg(1, largo)]);
    const titulo = getSession("s1")!.title;
    // 60 chars + elipsis.
    expect(titulo).toBe(`${"a".repeat(60)}…`);
    expect([...titulo].length).toBe(61);
  });

  it("deleteSession elimina la sesión y limpia la actual si coincide", async () => {
    const { saveSession, deleteSession, getSession, setCurrentSessionId } =
      await freshStorage();
    saveSession("s1", [userMsg(1, "hola")]);
    setCurrentSessionId("s1");
    expect(localStorage.getItem(CURRENT_SESSION_KEY)).toBe("s1");

    deleteSession("s1");
    expect(getSession("s1")).toBeNull();
    expect(localStorage.getItem(CURRENT_SESSION_KEY)).toBeNull();
  });

  it("deleteSession no toca la sesión actual si no coincide", async () => {
    const { saveSession, deleteSession, setCurrentSessionId } =
      await freshStorage();
    saveSession("s1", [userMsg(1, "hola")]);
    saveSession("s2", [userMsg(2, "adios")]);
    setCurrentSessionId("s2");

    deleteSession("s1");
    expect(localStorage.getItem(CURRENT_SESSION_KEY)).toBe("s2");
  });
});

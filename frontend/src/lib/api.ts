export type ChatRole = "user" | "assistant";

export interface ChatMessage {
  role: ChatRole;
  content: string;
}

export interface TextBlock {
  type: "text";
  content: string;
}

export interface ChartBlock {
  type: "chart";
  variant: "bar" | "radar";
  title?: string | null;
  data: Array<Record<string, unknown>>;
  keys?: string[] | null;
  x_key?: string | null;
}

export interface TableBlock {
  type: "table";
  title?: string | null;
  columns: string[];
  rows: Array<Record<string, unknown>>;
}

export interface ImageBlock {
  type: "image";
  car_id: number;
  caption?: string | null;
  foto_url?: string | null;
}

export type Block = TextBlock | ChartBlock | TableBlock | ImageBlock;

export interface ChatResponse {
  blocks: Block[];
}

const API_URL =
  (import.meta.env.VITE_API_URL as string | undefined)?.replace(/\/$/, "") ??
  "http://localhost:8000";

export async function sendChat(messages: ChatMessage[]): Promise<ChatResponse> {
  const res = await fetch(`${API_URL}/chat`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ messages }),
  });

  if (!res.ok) {
    throw new Error(`HTTP ${res.status}`);
  }

  const data = (await res.json()) as ChatResponse;
  if (!data || !Array.isArray(data.blocks)) {
    throw new Error("Respuesta inválida del servidor");
  }
  return data;
}

/** Espejo del modelo Pydantic `Version` (backend/src/models/normalized.py). */
export interface Car {
  id: number;
  marca: string;
  modelo: string;
  submodelo: string;
  nombre: string;
  foto_url: string;
  plazas: number | null;
  longitud: number | null;
  anchura: number | null;
  altura: number | null;
  capacidad_maletero: number | null;
  carroceria: string;
  puertas: number | null;
  precio: number | null;
  fecha_inicio: string | null;
  fecha_fin: string | null;
  combustible: string | null;
  potencia: number | null;
  aceleracion: number | null;
  velocidad_maxima: number | null;
  peso: number | null;
  consumo_medio: number | null;
  traccion: string;
  transmision: string;
  numero_marchas: number | null;
  capacidad_deposito: number | null;
  url: string;
}

/** Respuesta de `GET /api/filters/meta`. */
export interface FiltersMeta {
  marca: string[];
  combustible: string[];
  carroceria: string[];
  traccion: string[];
  transmision: string[];
}

/** Filtros que `GET /api/cars` acepta como query params. */
export interface CatalogFilters {
  marca?: string;
  modelo?: string;
  combustible?: string;
  carroceria?: string;
  traccion?: string;
  transmision?: string;
  precio_min?: number;
  precio_max?: number;
  potencia_min?: number;
  plazas_min?: number;
}

export async function fetchFiltersMeta(): Promise<FiltersMeta> {
  const res = await fetch(`${API_URL}/api/filters/meta`);
  if (!res.ok) {
    throw new Error(`HTTP ${res.status}`);
  }
  return (await res.json()) as FiltersMeta;
}

export async function fetchCars(
  filters: CatalogFilters,
  limit: number,
  offset: number,
): Promise<Car[]> {
  const params = new URLSearchParams();
  for (const [key, value] of Object.entries(filters)) {
    if (value !== undefined && value !== null && value !== "") {
      params.set(key, String(value));
    }
  }
  params.set("limit", String(limit));
  params.set("offset", String(offset));

  const res = await fetch(`${API_URL}/api/cars?${params.toString()}`);
  if (!res.ok) {
    throw new Error(`HTTP ${res.status}`);
  }
  return (await res.json()) as Car[];
}

export async function fetchCar(id: number): Promise<Car> {
  const res = await fetch(`${API_URL}/api/cars/${id}`);
  if (!res.ok) {
    throw new Error(`HTTP ${res.status}`);
  }
  return (await res.json()) as Car;
}

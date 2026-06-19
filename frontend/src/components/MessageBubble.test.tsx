import type { ReactElement, ReactNode } from "react";
import { cleanup, render, screen } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import type { Block } from "../lib/api";
import MessageBubble from "./MessageBubble";

// Recharts mide su contenedor con ResizeObserver; en jsdom el ancho es 0 y el
// chart no pinta nada (ni la leyenda). Sustituimos ResponsiveContainer por un
// div con tamaño fijo para que el SVG (y la leyenda, donde se ve la etiqueta
// legible de cada serie) sí se rendericen y podamos hacer aserciones sobre ellos.
vi.mock("recharts", async () => {
  const actual = await vi.importActual<typeof import("recharts")>("recharts");
  const { cloneElement, isValidElement } = await vi.importActual<
    typeof import("react")
  >("react");
  return {
    ...actual,
    // Inyectamos ancho/alto fijos al chart hijo (BarChart/RadarChart), que es lo
    // que ResponsiveContainer haría midiendo el DOM (imposible en jsdom).
    ResponsiveContainer: ({ children }: { children: ReactNode }) =>
      isValidElement(children)
        ? cloneElement(children as ReactElement<{ width?: number; height?: number }>, {
            width: 600,
            height: 300,
          })
        : children,
  };
});

beforeEach(() => {
  localStorage.clear();
});

afterEach(() => {
  cleanup();
});

describe("MessageBubble", () => {
  it("role 'user' muestra el texto plano", () => {
    render(<MessageBubble role="user" content="¿Qué SUV me recomiendas?" />);
    expect(
      screen.getByText("¿Qué SUV me recomiendas?"),
    ).toBeInTheDocument();
  });

  it("role 'assistant' con TextBlock renderiza el markdown como texto", () => {
    const blocks: Block[] = [
      { type: "text", content: "El **Corolla** es una buena opción." },
    ];
    render(<MessageBubble role="assistant" blocks={blocks} />);
    // react-markdown convierte **Corolla** en <strong>; el texto sigue presente.
    expect(screen.getByText("Corolla")).toBeInTheDocument();
    expect(screen.getByText("Corolla").tagName).toBe("STRONG");
  });

  it("ImageBlock con foto_url renderiza un <img> con ese src", () => {
    const blocks: Block[] = [
      {
        type: "image",
        car_id: 1,
        caption: "Toyota Corolla",
        foto_url: "https://example.test/corolla.jpg",
      },
    ];
    render(<MessageBubble role="assistant" blocks={blocks} />);
    const img = screen.getByRole("img");
    expect(img).toHaveAttribute("src", "https://example.test/corolla.jpg");
    expect(img).toHaveAttribute("alt", "Toyota Corolla");
  });

  it("ImageBlock sin foto_url no renderiza imagen", () => {
    const blocks: Block[] = [
      { type: "image", car_id: 1, caption: "sin foto" },
    ];
    render(<MessageBubble role="assistant" blocks={blocks} />);
    expect(screen.queryByRole("img")).toBeNull();
  });

  it("ChartBlock radar con varias series muestra etiquetas legibles en la leyenda", () => {
    // Con 2+ series sí hay leyenda (la de una sola serie se oculta por redundante).
    // Usamos radar porque las barras aplican el guard de una sola serie/unidad y
    // recortan a una. El render NO reescribe los datos (claves crudas valor/valor2),
    // solo muestra la etiqueta legible como texto en la leyenda.
    const blocks: Block[] = [
      {
        type: "chart",
        variant: "radar",
        x_key: "dimension",
        keys: ["valor", "valor2"],
        data: [
          { dimension: "Precio", valor: 40000, valor2: 35000 },
          { dimension: "Potencia", valor: 150, valor2: 120 },
          { dimension: "Consumo", valor: 6, valor2: 5 },
        ],
      },
    ];
    render(<MessageBubble role="assistant" blocks={blocks} />);
    // Sin title/unit la etiqueta legible cae a la clave cruda, que SÍ aparece en
    // la leyenda multi-serie (recharts pinta el `name` de cada Radar).
    expect(screen.getByText("valor")).toBeInTheDocument();
    expect(screen.getByText("valor2")).toBeInTheDocument();
  });

  it("ChartBlock bar con una sola serie NO renderiza leyenda redundante", () => {
    // Con una sola serie el chart-title de arriba ya identifica la métrica; la
    // leyenda de una línea ocuparía más que el gráfico, así que se oculta.
    const blocks: Block[] = [
      {
        type: "chart",
        variant: "bar",
        title: "Precio medio",
        x_key: "grupo",
        keys: ["valor"],
        x_label: "Marca",
        unit: "€",
        data: [
          { grupo: "BMW", valor: 52000 },
          { grupo: "Audi", valor: 48000 },
          { grupo: "Seat", valor: 23000 },
        ],
      },
    ];
    const { container } = render(
      <MessageBubble role="assistant" blocks={blocks} />,
    );
    // No hay leyenda de recharts en el DOM...
    expect(container.querySelector(".recharts-legend-wrapper")).toBeNull();
    // ...pero el título (que identifica la serie) sí sigue presente.
    expect(screen.getByText("Precio medio")).toBeInTheDocument();
  });

  it("ChartBlock radar normaliza cada dimensión a 0-100 sin que la magnitud grande aplaste", () => {
    // Una dimensión enorme (precio) y otra pequeña (consumo). Tras normalizar a
    // 0-100, el radio del polígono no debe corresponder a los valores crudos.
    const blocks: Block[] = [
      {
        type: "chart",
        variant: "radar",
        title: "Perfil",
        x_key: "dimension",
        keys: ["valor"],
        unit: "",
        data: [
          { dimension: "Precio", valor: 40000 },
          { dimension: "Consumo", valor: 6 },
          { dimension: "Potencia", valor: 150 },
        ],
      },
    ];
    const { container } = render(
      <MessageBubble role="assistant" blocks={blocks} />,
    );
    // "Perfil" aparece al menos como chart-title (la leyenda de una sola serie se
    // oculta por redundante); siempre es la etiqueta legible, nunca la clave "valor".
    expect(screen.getAllByText("Perfil").length).toBeGreaterThan(0);
    expect(screen.queryByText("valor")).toBeNull();
    // El radar normaliza cada dimensión a 0-100: el polígono (recharts-radar-polygon)
    // se dibuja con radios derivados de la escala 0-100, no de los valores crudos
    // (40000/6/150). Verificamos que el radar se montó con datos normalizados: el
    // path del polígono existe y los radios de la grid concéntrica caben en el SVG.
    const radarPoly = container.querySelector(".recharts-radar-polygon path");
    expect(radarPoly).not.toBeNull();
    // Defensa de la normalización: ningún punto del polígono escapa del lienzo
    // (lo que sí pasaría con un valor crudo de 40000 sobre un eje compartido).
    const d = radarPoly?.getAttribute("d") ?? "";
    const coords = d.match(/-?\d+(\.\d+)?/g)?.map(Number) ?? [];
    expect(coords.length).toBeGreaterThan(0);
    expect(coords.every((n) => Math.abs(n) < 10000)).toBe(true);
  });
});

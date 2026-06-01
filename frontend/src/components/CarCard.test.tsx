import { cleanup, render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import type { Car } from "../lib/api";

function fakeCar(overrides: Partial<Car> = {}): Car {
  return {
    id: 42,
    marca: "Toyota",
    modelo: "Corolla",
    submodelo: "",
    nombre: "Corolla 1.8 Hybrid",
    foto_url: "https://example.test/foto.jpg",
    plazas: 5,
    longitud: 4630,
    anchura: 1780,
    altura: 1435,
    capacidad_maletero: 471,
    carroceria: "berlina",
    puertas: 5,
    precio: 28500,
    fecha_inicio: null,
    fecha_fin: null,
    combustible: "hev_gasolina",
    potencia: 140,
    aceleracion: 9.2,
    velocidad_maxima: 180,
    peso: 1395,
    consumo_medio: 4.5,
    traccion: "delantera",
    transmision: "automático",
    numero_marchas: null,
    capacidad_deposito: 43,
    url: "https://example.test/ficha",
    ...overrides,
  };
}

// CarCard usa toggleFavorite/useFavorites del módulo storage, que cachea los
// favoritos en estado de módulo. Reimportamos en limpio por test para que el
// cache no arrastre estado entre casos.
async function renderCard(car: Car) {
  vi.resetModules();
  const { default: CarCard } = await import("./CarCard");
  return render(<CarCard car={car} />);
}

beforeEach(() => {
  localStorage.clear();
});

afterEach(() => {
  cleanup();
});

describe("CarCard", () => {
  it("muestra marca+modelo, precio formateado y combustible", async () => {
    await renderCard(fakeCar());

    expect(
      screen.getByRole("heading", { name: /Toyota Corolla/i }),
    ).toBeInTheDocument();
    expect(screen.getByText("Corolla 1.8 Hybrid")).toBeInTheDocument();
    // 28.500 € (sin decimales); no fijamos el separador exacto por locale.
    const precio = screen.getByText(/€/);
    expect(precio.textContent?.replace(/\D/g, "")).toBe("28500");
    // hev_gasolina -> etiqueta legible.
    expect(screen.getByText("Híbrido gasolina")).toBeInTheDocument();
  });

  it("renderiza el botón de favorito como no presionado por defecto", async () => {
    await renderCard(fakeCar());
    const btn = screen.getByRole("button", { name: /guardar en favoritos/i });
    expect(btn).toHaveAttribute("aria-pressed", "false");
  });

  it("al hacer click marca el coche como favorito (aria-pressed=true)", async () => {
    await renderCard(fakeCar({ id: 7 }));
    const btn = screen.getByRole("button");
    expect(btn).toHaveAttribute("aria-pressed", "false");

    await userEvent.click(btn);

    // Tras el toggle, el botón pasa a estado presionado y cambia su etiqueta.
    const presionado = screen.getByRole("button", {
      name: /quitar de favoritos/i,
    });
    expect(presionado).toHaveAttribute("aria-pressed", "true");
    // Y queda persistido en localStorage.
    expect(localStorage.getItem("autoai.favorites.v1")).toContain("7");
  });
});

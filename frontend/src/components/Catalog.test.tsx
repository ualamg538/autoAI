import { cleanup, render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import type { Car } from "../lib/api";

// fetchCars / fetchFiltersMeta viven en ../lib/api; los mockeamos para controlar
// cuántos coches devuelve cada página sin tocar la red.
const { fetchCars, fetchFiltersMeta } = vi.hoisted(() => ({
  fetchCars: vi.fn(),
  fetchFiltersMeta: vi.fn(),
}));

vi.mock("../lib/api", () => ({
  fetchCars,
  fetchFiltersMeta,
}));

import Catalog from "./Catalog";

const PAGE_SIZE = 24;

function fakeCar(id: number): Car {
  return {
    id,
    marca: "Marca",
    modelo: `Modelo ${id}`,
    submodelo: "",
    nombre: `Coche ${id}`,
    foto_url: "https://example.test/foto.jpg",
    plazas: 5,
    longitud: 4000,
    anchura: 1800,
    altura: 1500,
    capacidad_maletero: 400,
    carroceria: "berlina",
    puertas: 5,
    precio: 20000,
    fecha_inicio: null,
    fecha_fin: null,
    combustible: "gasolina",
    potencia: 100,
    aceleracion: 10,
    velocidad_maxima: 200,
    peso: 1200,
    consumo_medio: 6,
    traccion: "delantera",
    transmision: "manual",
    numero_marchas: 6,
    capacidad_deposito: 50,
    url: "https://example.test/ficha",
  };
}

function page(n: number): Car[] {
  return Array.from({ length: n }, (_, i) => fakeCar(i + 1));
}

function prevButton() {
  return screen.getByRole("button", { name: /anterior/i });
}
function nextButton() {
  return screen.getByRole("button", { name: /siguiente/i });
}

beforeEach(() => {
  localStorage.clear();
  fetchCars.mockReset();
  fetchFiltersMeta.mockReset();
  // El catálogo pide la meta de filtros al montar; devolvemos algo válido.
  fetchFiltersMeta.mockResolvedValue({
    marca: [],
    combustible: [],
    carroceria: [],
    traccion: [],
    transmision: [],
  });
});

afterEach(() => {
  cleanup();
});

describe("Catalog: paginación", () => {
  it("página llena (24) habilita 'Siguiente' y deshabilita 'Anterior' en offset 0", async () => {
    fetchCars.mockResolvedValue(page(PAGE_SIZE));
    render(<Catalog />);

    await waitFor(() => expect(nextButton()).toBeEnabled());
    expect(prevButton()).toBeDisabled();
  });

  it("página parcial (<24) deshabilita 'Siguiente'", async () => {
    fetchCars.mockResolvedValue(page(10));
    render(<Catalog />);

    await waitFor(() => expect(prevButton()).toBeInTheDocument());
    expect(nextButton()).toBeDisabled();
  });

  it("al avanzar de página 'Anterior' se habilita y se pide el offset siguiente", async () => {
    // Página 1 y 2 llenas.
    fetchCars.mockResolvedValue(page(PAGE_SIZE));
    render(<Catalog />);

    await waitFor(() => expect(nextButton()).toBeEnabled());
    expect(fetchCars).toHaveBeenLastCalledWith(expect.anything(), PAGE_SIZE, 0);

    await userEvent.click(nextButton());

    await waitFor(() => expect(prevButton()).toBeEnabled());
    expect(fetchCars).toHaveBeenLastCalledWith(
      expect.anything(),
      PAGE_SIZE,
      PAGE_SIZE,
    );
    expect(screen.getByText("Página 2")).toBeInTheDocument();
  });

  it("total múltiplo de PAGE_SIZE: la página siguiente vacía retrocede el offset", async () => {
    // offset 0 -> página llena; offset 24 -> vacía (el total era 24 exacto).
    fetchCars.mockImplementation((_f: unknown, _l: number, offset: number) =>
      Promise.resolve(offset === 0 ? page(PAGE_SIZE) : []),
    );
    render(<Catalog />);

    await waitFor(() => expect(nextButton()).toBeEnabled());
    expect(screen.getByText("Página 1")).toBeInTheDocument();

    await userEvent.click(nextButton());

    // El efecto pide offset 24, recibe [] y, como offset>0, retrocede a 0:
    // vuelve a pedir offset 0 y se queda en la página 1 (no en una vacía).
    await waitFor(() =>
      expect(fetchCars).toHaveBeenCalledWith(expect.anything(), PAGE_SIZE, 0),
    );
    await waitFor(() =>
      expect(fetchCars).toHaveBeenCalledWith(
        expect.anything(),
        PAGE_SIZE,
        PAGE_SIZE,
      ),
    );
    await waitFor(() =>
      expect(screen.getByText("Página 1")).toBeInTheDocument(),
    );
    // La última llamada a fetchCars fue la de retroceso (offset 0).
    expect(fetchCars).toHaveBeenLastCalledWith(expect.anything(), PAGE_SIZE, 0);
    // Y no quedan tarjetas de una página vacía: hay 24.
    expect(screen.getAllByRole("article")).toHaveLength(PAGE_SIZE);
  });
});

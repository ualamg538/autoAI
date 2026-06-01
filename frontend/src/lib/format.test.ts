import { describe, expect, it } from "vitest";
import { formatCombustible, formatNumero, formatPrecio } from "./format";

describe("formatCombustible", () => {
  it("devuelve el guion para valores vacíos", () => {
    expect(formatCombustible(null)).toBe("—");
    expect(formatCombustible(undefined)).toBe("—");
    expect(formatCombustible("")).toBe("—");
  });

  it("traduce claves conocidas a su etiqueta", () => {
    expect(formatCombustible("gasoleo")).toBe("Diésel");
    expect(formatCombustible("phev_gasolina")).toBe(
      "Híbrido enchufable gasolina",
    );
  });

  it("devuelve el valor original si la clave es desconocida", () => {
    expect(formatCombustible("hidrogeno")).toBe("hidrogeno");
  });
});

describe("formatPrecio", () => {
  it("indica precio no disponible cuando es null/undefined", () => {
    expect(formatPrecio(null)).toBe("Precio no disponible");
    expect(formatPrecio(undefined)).toBe("Precio no disponible");
  });

  it("formatea como EUR sin decimales y con separador de miles", () => {
    const out = formatPrecio(15000);
    // No fijamos el separador exacto (depende del locale del runtime), pero sí
    // que están todos los dígitos agrupados y el símbolo de euro, y que no hay
    // parte decimal.
    expect(out).toContain("€");
    expect(out.replace(/\D/g, "")).toBe("15000");
    expect(out).not.toContain(",00");
  });

  it("formatea el cero como un precio válido (no 'no disponible')", () => {
    const out = formatPrecio(0);
    expect(out).toContain("€");
    expect(out).toContain("0");
  });
});

describe("formatNumero", () => {
  it("devuelve el guion para null/undefined", () => {
    expect(formatNumero(null)).toBe("—");
    expect(formatNumero(undefined)).toBe("—");
  });

  it("formatea un número sin sufijo", () => {
    expect(formatNumero(5)).toBe("5");
  });

  it("añade el sufijo cuando se indica", () => {
    expect(formatNumero(150, " CV")).toBe("150 CV");
  });

  it("trata el cero como número válido", () => {
    expect(formatNumero(0)).toBe("0");
  });
});

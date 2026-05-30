// Helpers de presentación compartidos por Catálogo / Favoritos / tarjetas.

// `combustible` en BD usa el vocabulario canónico de normalized.py.
// Aquí solo se traduce para mostrar; el valor enviado al backend no cambia.
const COMBUSTIBLE_LABELS: Record<string, string> = {
  gasolina: "Gasolina",
  gasoleo: "Diésel",
  gas: "Gas (GLP/GNC)",
  electrico: "Eléctrico",
  mhev_gasolina: "Microhíbrido gasolina",
  mhev_gasoleo: "Microhíbrido diésel",
  hev_gasolina: "Híbrido gasolina",
  phev_gasolina: "Híbrido enchufable gasolina",
  phev_gasoleo: "Híbrido enchufable diésel",
};

export function formatCombustible(value: string | null | undefined): string {
  if (!value) return "—";
  return COMBUSTIBLE_LABELS[value] ?? value;
}

export function formatPrecio(value: number | null | undefined): string {
  if (value == null) return "Precio no disponible";
  return new Intl.NumberFormat("es-ES", {
    style: "currency",
    currency: "EUR",
    maximumFractionDigits: 0,
  }).format(value);
}

export function formatNumero(
  value: number | null | undefined,
  sufijo = "",
): string {
  if (value == null) return "—";
  return `${new Intl.NumberFormat("es-ES").format(value)}${sufijo}`;
}

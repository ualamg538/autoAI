// Helpers de presentación compartidos por Catálogo / Favoritos / tarjetas.
//
// No son componentes React, así que para traducir usan la instancia de i18next
// directamente (i18n.t), no el hook useTranslation. Las etiquetas describen el
// *valor del enum* de combustible para la UI; no son datos crudos del coche, así
// que sí se localizan (el valor crudo enviado al backend, p. ej. "gasoleo", no
// cambia).

import i18n from "./i18n";

export function formatCombustible(value: string | null | undefined): string {
  if (!value) return i18n.t("common.dash");
  const key = `format.fuel.${value}`;
  // Clave desconocida (enum nuevo aún sin traducir) → devuelve el valor crudo,
  // no la clave i18n.
  return i18n.exists(key) ? i18n.t(key) : value;
}

export function formatPrecio(value: number | null | undefined): string {
  if (value == null) return i18n.t("format.priceUnavailable");
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
  if (value == null) return i18n.t("common.dash");
  return `${new Intl.NumberFormat("es-ES").format(value)}${sufijo}`;
}

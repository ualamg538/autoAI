// Setup global para Vitest: matchers de jest-dom (toBeInTheDocument, etc.) y un
// stub de ResizeObserver, que jsdom no implementa y que Recharts
// (ResponsiveContainer) exige. Los tests de render evitan charts a propósito,
// pero el stub deja la puerta abierta sin que el entorno reviente.
import '@testing-library/jest-dom/vitest'

// Inicializa i18next para los tests. El idioma inicial sale de prefs (vacías en
// jsdom → "es"), así que t()/useTranslation() resuelven al español y las
// aserciones sobre literales en castellano siguen siendo válidas. Sin este
// import, format.ts (que usa i18n.t) devolvería las claves crudas.
import './../lib/i18n'

class ResizeObserverStub {
  observe() {}
  unobserve() {}
  disconnect() {}
}

if (!('ResizeObserver' in globalThis)) {
  globalThis.ResizeObserver =
    ResizeObserverStub as unknown as typeof ResizeObserver
}

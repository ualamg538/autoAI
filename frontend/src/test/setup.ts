// Setup global para Vitest: matchers de jest-dom (toBeInTheDocument, etc.) y un
// stub de ResizeObserver, que jsdom no implementa y que Recharts
// (ResponsiveContainer) exige. Los tests de render evitan charts a propósito,
// pero el stub deja la puerta abierta sin que el entorno reviente.
import '@testing-library/jest-dom/vitest'

class ResizeObserverStub {
  observe() {}
  unobserve() {}
  disconnect() {}
}

if (!('ResizeObserver' in globalThis)) {
  globalThis.ResizeObserver =
    ResizeObserverStub as unknown as typeof ResizeObserver
}

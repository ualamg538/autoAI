import { useEffect, useState, type FormEvent } from "react";
import {
  fetchCars,
  fetchFiltersMeta,
  type Car,
  type CatalogFilters,
  type FiltersMeta,
} from "../lib/api";
import { formatCombustible } from "../lib/format";
import CarCard from "./CarCard";

const PAGE_SIZE = 24;

function parseNum(value: string): number | undefined {
  if (value.trim() === "") return undefined;
  const n = Number(value);
  return Number.isFinite(n) ? n : undefined;
}

export default function Catalog() {
  const [meta, setMeta] = useState<FiltersMeta | null>(null);
  const [filters, setFilters] = useState<CatalogFilters>({});
  const [applied, setApplied] = useState<CatalogFilters>({});
  const [offset, setOffset] = useState(0);
  const [cars, setCars] = useState<Car[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(false);

  useEffect(() => {
    fetchFiltersMeta()
      .then(setMeta)
      .catch(() => setMeta(null));
  }, []);

  useEffect(() => {
    let cancelled = false;
    fetchCars(applied, PAGE_SIZE, offset)
      .then((data) => {
        if (cancelled) return;
        // El total puede ser múltiplo exacto de PAGE_SIZE: en ese caso la
        // página siguiente llega vacía. Si pasa y no estamos en la primera,
        // retrocedemos en vez de mostrar una página vacía.
        if (data.length === 0 && offset > 0) {
          setOffset((o) => Math.max(0, o - PAGE_SIZE));
          return;
        }
        setCars(data);
        setError(false);
      })
      .catch(() => {
        if (!cancelled) {
          setCars([]);
          setError(true);
        }
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });
    return () => {
      cancelled = true;
    };
  }, [applied, offset]);

  function reloadWith(nextFilters: CatalogFilters, nextOffset: number) {
    setLoading(true);
    setApplied(nextFilters);
    setOffset(nextOffset);
  }

  function onSubmit(e: FormEvent) {
    e.preventDefault();
    reloadWith({ ...filters }, 0);
  }

  function onReset() {
    setFilters({});
    reloadWith({}, 0);
  }

  function goToPage(nextOffset: number) {
    setLoading(true);
    setOffset(nextOffset);
  }

  function setField<K extends keyof CatalogFilters>(
    key: K,
    value: CatalogFilters[K],
  ) {
    setFilters((f) => {
      const next = { ...f };
      if (value === undefined) {
        delete next[key];
      } else {
        next[key] = value;
      }
      return next;
    });
  }

  const page = Math.floor(offset / PAGE_SIZE) + 1;
  const canPrev = offset > 0;
  const canNext = cars.length === PAGE_SIZE;

  return (
    <div className="catalog">
      <form className="catalog-filters" onSubmit={onSubmit}>
        <div className="filter-field">
          <label htmlFor="f-marca">Marca</label>
          <select
            id="f-marca"
            value={filters.marca ?? ""}
            onChange={(e) => setField("marca", e.target.value || undefined)}
          >
            <option value="">Todas</option>
            {meta?.marca.map((m) => (
              <option key={m} value={m}>
                {m}
              </option>
            ))}
          </select>
        </div>

        <div className="filter-field">
          <label htmlFor="f-combustible">Combustible</label>
          <select
            id="f-combustible"
            value={filters.combustible ?? ""}
            onChange={(e) =>
              setField("combustible", e.target.value || undefined)
            }
          >
            <option value="">Todos</option>
            {meta?.combustible.map((c) => (
              <option key={c} value={c}>
                {formatCombustible(c)}
              </option>
            ))}
          </select>
        </div>

        <div className="filter-field">
          <label htmlFor="f-carroceria">Carrocería</label>
          <select
            id="f-carroceria"
            value={filters.carroceria ?? ""}
            onChange={(e) =>
              setField("carroceria", e.target.value || undefined)
            }
          >
            <option value="">Todas</option>
            {meta?.carroceria.map((c) => (
              <option key={c} value={c}>
                {c}
              </option>
            ))}
          </select>
        </div>

        <div className="filter-field">
          <label htmlFor="f-traccion">Tracción</label>
          <select
            id="f-traccion"
            value={filters.traccion ?? ""}
            onChange={(e) => setField("traccion", e.target.value || undefined)}
          >
            <option value="">Todas</option>
            {meta?.traccion.map((t) => (
              <option key={t} value={t}>
                {t}
              </option>
            ))}
          </select>
        </div>

        <div className="filter-field">
          <label htmlFor="f-transmision">Transmisión</label>
          <select
            id="f-transmision"
            value={filters.transmision ?? ""}
            onChange={(e) =>
              setField("transmision", e.target.value || undefined)
            }
          >
            <option value="">Todas</option>
            {meta?.transmision.map((t) => (
              <option key={t} value={t}>
                {t}
              </option>
            ))}
          </select>
        </div>

        <div className="filter-field">
          <label htmlFor="f-modelo">Modelo</label>
          <input
            id="f-modelo"
            type="text"
            placeholder="p. ej. corolla"
            value={filters.modelo ?? ""}
            onChange={(e) => setField("modelo", e.target.value || undefined)}
          />
        </div>

        <div className="filter-field">
          <label htmlFor="f-precio-min">Precio mín. (€)</label>
          <input
            id="f-precio-min"
            type="number"
            min={0}
            value={filters.precio_min ?? ""}
            onChange={(e) =>
              setField("precio_min", parseNum(e.target.value))
            }
          />
        </div>

        <div className="filter-field">
          <label htmlFor="f-precio-max">Precio máx. (€)</label>
          <input
            id="f-precio-max"
            type="number"
            min={0}
            value={filters.precio_max ?? ""}
            onChange={(e) =>
              setField("precio_max", parseNum(e.target.value))
            }
          />
        </div>

        <div className="filter-field">
          <label htmlFor="f-potencia-min">Potencia mín. (CV)</label>
          <input
            id="f-potencia-min"
            type="number"
            min={0}
            value={filters.potencia_min ?? ""}
            onChange={(e) =>
              setField("potencia_min", parseNum(e.target.value))
            }
          />
        </div>

        <div className="filter-field">
          <label htmlFor="f-plazas-min">Plazas mín.</label>
          <input
            id="f-plazas-min"
            type="number"
            min={0}
            value={filters.plazas_min ?? ""}
            onChange={(e) =>
              setField("plazas_min", parseNum(e.target.value))
            }
          />
        </div>

        <div className="filter-actions">
          <button type="submit" className="btn-primary">
            Aplicar filtros
          </button>
          <button type="button" className="btn-ghost" onClick={onReset}>
            Limpiar
          </button>
        </div>
      </form>

      <div className="catalog-results">
        {loading ? (
          <p className="catalog-status">Cargando coches…</p>
        ) : error ? (
          <p className="catalog-status error">
            No se pudo cargar el catálogo. Inténtalo de nuevo.
          </p>
        ) : cars.length === 0 ? (
          <p className="catalog-status">
            Ningún coche coincide con esos filtros.
          </p>
        ) : (
          <>
            <div className="car-grid">
              {cars.map((c) => (
                <CarCard key={c.id} car={c} />
              ))}
            </div>
            <div className="catalog-pagination">
              <button
                type="button"
                className="btn-ghost"
                disabled={!canPrev}
                onClick={() => goToPage(Math.max(0, offset - PAGE_SIZE))}
              >
                ← Anterior
              </button>
              <span>Página {page}</span>
              <button
                type="button"
                className="btn-ghost"
                disabled={!canNext}
                onClick={() => goToPage(offset + PAGE_SIZE)}
              >
                Siguiente →
              </button>
            </div>
          </>
        )}
      </div>
    </div>
  );
}

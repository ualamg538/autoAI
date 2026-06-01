import { useEffect, useState, type FormEvent } from "react";
import { AlertCircle, SearchX } from "lucide-react";
import { useTranslation } from "react-i18next";
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

// Rejilla de placeholders mientras carga la primera página de resultados.
function CarGridSkeleton() {
  return (
    <div className="car-grid" aria-hidden>
      {Array.from({ length: 8 }, (_, i) => (
        <div key={i} className="car-card-skeleton">
          <div className="sk-media" />
          <div className="sk-body">
            <div className="sk-line sk-title" />
            <div className="sk-line sk-sub" />
            <div className="sk-line sk-price" />
          </div>
        </div>
      ))}
    </div>
  );
}

function parseNum(value: string): number | undefined {
  if (value.trim() === "") return undefined;
  const n = Number(value);
  return Number.isFinite(n) ? n : undefined;
}

export default function Catalog() {
  const { t } = useTranslation();
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
          <label htmlFor="f-marca">{t("catalog.brand")}</label>
          <select
            id="f-marca"
            value={filters.marca ?? ""}
            onChange={(e) => setField("marca", e.target.value || undefined)}
          >
            <option value="">{t("catalog.optionAllF")}</option>
            {meta?.marca.map((m) => (
              <option key={m} value={m}>
                {m}
              </option>
            ))}
          </select>
        </div>

        <div className="filter-field">
          <label htmlFor="f-combustible">{t("catalog.fuel")}</label>
          <select
            id="f-combustible"
            value={filters.combustible ?? ""}
            onChange={(e) =>
              setField("combustible", e.target.value || undefined)
            }
          >
            <option value="">{t("catalog.optionAllM")}</option>
            {meta?.combustible.map((c) => (
              <option key={c} value={c}>
                {formatCombustible(c)}
              </option>
            ))}
          </select>
        </div>

        <div className="filter-field">
          <label htmlFor="f-carroceria">{t("catalog.bodywork")}</label>
          <select
            id="f-carroceria"
            value={filters.carroceria ?? ""}
            onChange={(e) =>
              setField("carroceria", e.target.value || undefined)
            }
          >
            <option value="">{t("catalog.optionAllF")}</option>
            {meta?.carroceria.map((c) => (
              <option key={c} value={c}>
                {c}
              </option>
            ))}
          </select>
        </div>

        <div className="filter-field">
          <label htmlFor="f-traccion">{t("catalog.traction")}</label>
          <select
            id="f-traccion"
            value={filters.traccion ?? ""}
            onChange={(e) => setField("traccion", e.target.value || undefined)}
          >
            <option value="">{t("catalog.optionAllF")}</option>
            {meta?.traccion.map((tr) => (
              <option key={tr} value={tr}>
                {tr}
              </option>
            ))}
          </select>
        </div>

        <div className="filter-field">
          <label htmlFor="f-transmision">{t("catalog.transmission")}</label>
          <select
            id="f-transmision"
            value={filters.transmision ?? ""}
            onChange={(e) =>
              setField("transmision", e.target.value || undefined)
            }
          >
            <option value="">{t("catalog.optionAllF")}</option>
            {meta?.transmision.map((tr) => (
              <option key={tr} value={tr}>
                {tr}
              </option>
            ))}
          </select>
        </div>

        <div className="filter-field">
          <label htmlFor="f-modelo">{t("catalog.model")}</label>
          <input
            id="f-modelo"
            type="text"
            placeholder={t("catalog.modelPlaceholder")}
            value={filters.modelo ?? ""}
            onChange={(e) => setField("modelo", e.target.value || undefined)}
          />
        </div>

        <div className="filter-field">
          <label htmlFor="f-precio-min">{t("catalog.priceMin")}</label>
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
          <label htmlFor="f-precio-max">{t("catalog.priceMax")}</label>
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
          <label htmlFor="f-potencia-min">{t("catalog.powerMin")}</label>
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
          <label htmlFor="f-plazas-min">{t("catalog.seatsMin")}</label>
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
            {t("catalog.apply")}
          </button>
          <button type="button" className="btn-ghost" onClick={onReset}>
            {t("catalog.clear")}
          </button>
        </div>
      </form>

      <div className="catalog-results">
        {loading ? (
          <CarGridSkeleton />
        ) : error ? (
          <div className="state-block state-error">
            <span className="state-icon">
              <AlertCircle size={24} aria-hidden />
            </span>
            <p className="state-text">{t("catalog.errorText")}</p>
            <button
              type="button"
              className="btn-primary"
              onClick={() => reloadWith(applied, offset)}
            >
              {t("common.retry")}
            </button>
          </div>
        ) : cars.length === 0 ? (
          <div className="state-block state-empty">
            <span className="state-icon">
              <SearchX size={24} aria-hidden />
            </span>
            <p className="state-text">{t("catalog.emptyText")}</p>
          </div>
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
                {t("catalog.prev")}
              </button>
              <span>{t("catalog.page", { page })}</span>
              <button
                type="button"
                className="btn-ghost"
                disabled={!canNext}
                onClick={() => goToPage(offset + PAGE_SIZE)}
              >
                {t("catalog.next")}
              </button>
            </div>
          </>
        )}
      </div>
    </div>
  );
}

import { useEffect, useState } from "react";
import { fetchCar, type Car } from "../lib/api";
import { useFavorites } from "../lib/storage";
import CarCard from "./CarCard";

export default function Favorites() {
  const ids = useFavorites();
  const [cache, setCache] = useState<Record<number, Car>>({});

  useEffect(() => {
    const missing = ids.filter((id) => !(id in cache));
    if (missing.length === 0) return;
    let cancelled = false;
    Promise.all(
      missing.map((id) =>
        fetchCar(id)
          .then((car) => [id, car] as const)
          .catch(() => null),
      ),
    ).then((results) => {
      if (cancelled) return;
      setCache((prev) => {
        const next = { ...prev };
        for (const r of results) {
          if (r) next[r[0]] = r[1];
        }
        return next;
      });
    });
    return () => {
      cancelled = true;
    };
  }, [ids, cache]);

  if (ids.length === 0) {
    return (
      <div className="aux-view">
        <div className="aux-empty">
          No tienes coches guardados. Pulsa el corazón en cualquier coche del
          catálogo o del chat para añadirlo.
        </div>
      </div>
    );
  }

  const cars = ids
    .map((id) => cache[id])
    .filter((c): c is Car => Boolean(c));
  const pending = cars.length < ids.length;

  return (
    <div className="aux-view">
      <h2 className="aux-title">Favoritos</h2>
      {cars.length === 0 ? (
        <p className="catalog-status">Cargando favoritos…</p>
      ) : (
        <>
          <div className="car-grid">
            {cars.map((c) => (
              <CarCard key={c.id} car={c} />
            ))}
          </div>
          {pending ? (
            <p className="catalog-status">Cargando más favoritos…</p>
          ) : null}
        </>
      )}
    </div>
  );
}

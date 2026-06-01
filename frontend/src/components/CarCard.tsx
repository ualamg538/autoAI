import { Heart } from "lucide-react";
import type { Car } from "../lib/api";
import { formatCombustible, formatNumero, formatPrecio } from "../lib/format";
import { toggleFavorite, useFavorites } from "../lib/storage";

export default function CarCard({ car }: { car: Car }) {
  const favorites = useFavorites();
  const fav = favorites.includes(car.id);

  return (
    <article className="car-card">
      <button
        type="button"
        className={`fav-btn${fav ? " active" : ""}`}
        aria-pressed={fav}
        aria-label={fav ? "Quitar de favoritos" : "Guardar en favoritos"}
        title={fav ? "Quitar de favoritos" : "Guardar en favoritos"}
        onClick={() => toggleFavorite(car.id)}
      >
        <Heart size={16} aria-hidden fill={fav ? "currentColor" : "none"} />
      </button>
      <a
        className="car-card-media"
        href={car.url}
        target="_blank"
        rel="noreferrer"
      >
        <img src={car.foto_url} alt={car.nombre} loading="lazy" />
      </a>
      <div className="car-card-body">
        <h3 className="car-card-title">
          {car.marca} {car.modelo}
        </h3>
        <p className="car-card-sub">{car.nombre}</p>
        <p className="car-card-price">{formatPrecio(car.precio)}</p>
        <dl className="car-card-specs">
          <div>
            <dt>Combustible</dt>
            <dd>{formatCombustible(car.combustible)}</dd>
          </div>
          <div>
            <dt>Potencia</dt>
            <dd>{formatNumero(car.potencia, " CV")}</dd>
          </div>
          <div>
            <dt>Carrocería</dt>
            <dd>{car.carroceria || "—"}</dd>
          </div>
          <div>
            <dt>Plazas</dt>
            <dd>{formatNumero(car.plazas)}</dd>
          </div>
        </dl>
      </div>
    </article>
  );
}

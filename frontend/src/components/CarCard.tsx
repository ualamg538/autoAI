import { Heart } from "lucide-react";
import { useTranslation } from "react-i18next";
import type { Car } from "../lib/api";
import { formatCombustible, formatNumero, formatPrecio } from "../lib/format";
import { toggleFavorite, useFavorites } from "../lib/storage";

export default function CarCard({ car }: { car: Car }) {
  const { t } = useTranslation();
  const favorites = useFavorites();
  const fav = favorites.includes(car.id);
  const favLabel = fav ? t("favorite.remove") : t("favorite.add");

  return (
    <article className="car-card">
      <button
        type="button"
        className={`fav-btn${fav ? " active" : ""}`}
        aria-pressed={fav}
        aria-label={favLabel}
        title={favLabel}
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
            <dt>{t("carCard.fuel")}</dt>
            <dd>{formatCombustible(car.combustible)}</dd>
          </div>
          <div>
            <dt>{t("carCard.power")}</dt>
            <dd>{formatNumero(car.potencia, " CV")}</dd>
          </div>
          <div>
            <dt>{t("carCard.bodywork")}</dt>
            <dd>{car.carroceria || t("common.dash")}</dd>
          </div>
          <div>
            <dt>{t("carCard.seats")}</dt>
            <dd>{formatNumero(car.plazas)}</dd>
          </div>
        </dl>
      </div>
    </article>
  );
}

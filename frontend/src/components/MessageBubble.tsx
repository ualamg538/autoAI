import type { ReactNode } from "react";
import { Heart } from "lucide-react";
import { useTranslation } from "react-i18next";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import {
  Bar,
  BarChart,
  CartesianGrid,
  Legend,
  PolarAngleAxis,
  PolarGrid,
  PolarRadiusAxis,
  Radar,
  RadarChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import type {
  Block,
  ChartBlock,
  ImageBlock,
  TableBlock,
  TextBlock,
} from "../lib/api";
import { toggleFavorite, useFavorites } from "../lib/storage";

type Role = "user" | "assistant";

interface UserBubbleProps {
  role: "user";
  content: string;
  isError?: boolean;
}

interface AssistantBubbleProps {
  role: "assistant";
  blocks: Block[];
  isError?: boolean;
}

type MessageBubbleProps = UserBubbleProps | AssistantBubbleProps;

// Lee una custom property de :root. Permite que los charts (que pintan en SVG y
// no heredan `currentColor` como los iconos) sigan al tema activo. Cae a un
// fallback cuando getComputedStyle no resuelve la variable (p. ej. en jsdom).
function cssVar(name: string, fallback: string): string {
  if (typeof window === "undefined") return fallback;
  const value = getComputedStyle(document.documentElement)
    .getPropertyValue(name)
    .trim();
  return value || fallback;
}

const CHART_FALLBACKS = ["#5e85b8", "#5fa977", "#d8a14a", "#9b7bc0", "#cf7a6b"];

function chartColors(): string[] {
  return CHART_FALLBACKS.map((fallback, i) =>
    cssVar(`--chart-${i + 1}`, fallback),
  );
}

// Barras: como mucho 10 elementos (ver Reglas de formato del prompt). Recortamos
// de forma determinista en el frontend para que un `agregar` con muchos grupos no
// genere una gráfica ilegible aunque el modelo no respete el tope.
const MAX_BARRAS = 10;

// Formateador de números con separador de miles (locale es-ES) para ejes/tooltip.
const numberFormat = new Intl.NumberFormat("es-ES", { maximumFractionDigits: 1 });

function formatearValor(valor: unknown, unit?: string | null): string {
  if (typeof valor !== "number" || !Number.isFinite(valor)) return String(valor ?? "");
  const num = numberFormat.format(valor);
  return unit ? `${num} ${unit}` : num;
}

// Etiqueta LEGIBLE de una serie a partir de los metadatos de presentación. NO
// toca los datos: `dataKey` sigue leyendo la clave cruda (p. ej. "valor"); esto
// solo produce el texto que se pinta en leyenda/tooltip. Prioridad: title+unit
// ("Precio medio (€)") > title > unit > la propia clave cruda como fallback.
function legibleParaSerie(
  key: string,
  title?: string | null,
  unit?: string | null,
): string {
  if (title && unit) return `${title} (${unit})`;
  if (title) return title;
  if (unit) return `${key} (${unit})`;
  return key;
}

// Abre los enlaces markdown en pestaña nueva. Compartido por TextBlockView y las
// celdas de tabla para no duplicar el override del ancla.
const MD_LINK_COMPONENT = {
  a: ({ children, href }: { children?: ReactNode; href?: string }) => (
    <a href={href} target="_blank" rel="noopener noreferrer">
      {children}
    </a>
  ),
};

// Componentes para las celdas de tabla: además del enlace, `p` colapsa el <p>
// que ReactMarkdown envuelve por defecto, para que el contenido quede inline
// dentro del <td> (las celdas sin markdown se ven igual que en texto plano).
const MD_CELL_COMPONENTS = {
  ...MD_LINK_COMPONENT,
  p: ({ children }: { children?: ReactNode }) => <>{children}</>,
};

function TextBlockView({ block }: { block: TextBlock }) {
  return (
    <ReactMarkdown
      remarkPlugins={[remarkGfm]}
      components={{
        ...MD_LINK_COMPONENT,
        table: ({ children }) => (
          <div className="md-table-wrap">
            <table className="md-table">{children}</table>
          </div>
        ),
      }}
    >
      {block.content}
    </ReactMarkdown>
  );
}

function ChartBlockView({ block }: { block: ChartBlock }) {
  const firstRow = block.data[0];
  const xKey =
    block.x_key ?? (firstRow ? Object.keys(firstRow)[0] : undefined) ?? "name";
  const allKeys =
    block.keys ?? (firstRow ? Object.keys(firstRow).filter((k) => k !== xKey) : []);

  // Colores y trazos leídos de los tokens para que los charts sigan al tema.
  const colors = chartColors();
  const gridStroke = cssVar("--border", "#e3e8ee");
  const axisStroke = cssVar("--text-soft", "#5b6675");

  if (block.variant === "bar") {
    // Una sola unidad/magnitud por gráfica de barras: si llegan varias series,
    // pintamos solo la primera. Mezclar precio (~40.000) con consumo (~6) deja
    // barras invisibles; mejor degradar a una serie coherente que algo ilegible.
    const keys = allKeys.slice(0, 1);
    const serieKey = keys[0];
    // Ordenamos de mayor a menor por la serie y recortamos a MAX_BARRAS, sin
    // mutar el array original. `serieKey` puede faltar si data viene vacío.
    const data = serieKey
      ? [...block.data]
          .sort((a, b) => Number(b[serieKey] ?? 0) - Number(a[serieKey] ?? 0))
          .slice(0, MAX_BARRAS)
      : block.data;
    const xLabel = block.x_label ?? xKey;
    // Con muchas categorías los ticks horizontales se solapan entre sí y con el
    // label del eje. A partir de ~7 los rotamos y reducimos su tamaño, y damos
    // más alto al XAxis + margen inferior para que el texto rotado no se corte.
    const muchasCategorias = data.length > 6;
    const xTickProps = muchasCategorias
      ? { angle: -40, textAnchor: "end" as const, fontSize: 11, height: 64 }
      : { fontSize: 12, height: 30 };
    // Leyenda redundante con una sola serie: el chart-title de arriba + la unidad
    // en eje Y/tooltip ya la identifican; ocultarla evita una línea que ocupa más
    // que el propio gráfico. Solo mostramos leyenda cuando hay 2+ series.
    const mostrarLeyenda = keys.length > 1;

    return (
      <div className="chart-block">
        {block.title ? <div className="chart-title">{block.title}</div> : null}
        <ResponsiveContainer width="100%" height={340}>
          <BarChart data={data} margin={{ bottom: muchasCategorias ? 28 : 16 }}>
            <CartesianGrid strokeDasharray="3 3" stroke={gridStroke} />
            <XAxis
              dataKey={xKey}
              stroke={axisStroke}
              interval={0}
              {...xTickProps}
              label={{
                value: xLabel,
                position: "insideBottom",
                offset: muchasCategorias ? -4 : -8,
                fill: axisStroke,
                fontSize: 12,
              }}
            />
            <YAxis
              stroke={axisStroke}
              fontSize={12}
              width={72}
              tickFormatter={(v) => numberFormat.format(Number(v))}
            />
            <Tooltip
              formatter={(value) => formatearValor(value, block.unit)}
            />
            {mostrarLeyenda ? <Legend /> : null}
            {keys.map((k, i) => (
              <Bar
                key={k}
                dataKey={k}
                name={legibleParaSerie(k, block.title, block.unit)}
                fill={colors[i % colors.length]}
                radius={[4, 4, 0, 0]}
              />
            ))}
          </BarChart>
        </ResponsiveContainer>
      </div>
    );
  }

  // Radar: cada dimensión (fila) se mide en su propia escala, así que un eje
  // radial compartido aplastaría las pequeñas. Normalizamos cada fila a 0-100
  // (min-max sobre las series de esa fila) en un `data` NUEVO para el render, y
  // guardamos los valores reales aparte para mostrarlos en el tooltip. Los datos
  // de origen no se tocan; solo cambia la escala visual.
  const keys = allKeys;
  // Valor real por (fila xKey, serie) para reconstruir el tooltip sin inventar.
  const realPorFila = new Map<string, Record<string, number>>();
  const dataNorm = block.data.map((row) => {
    const valores = keys
      .map((k) => Number(row[k]))
      .filter((n) => Number.isFinite(n));
    const min = valores.length ? Math.min(...valores) : 0;
    const max = valores.length ? Math.max(...valores) : 0;
    const span = max - min;
    const etiquetaFila = String(row[xKey] ?? "");
    const reales: Record<string, number> = {};
    const out: Record<string, unknown> = { [xKey]: row[xKey] };
    for (const k of keys) {
      const v = Number(row[k]);
      if (Number.isFinite(v)) {
        reales[k] = v;
        // span 0 (una sola serie o todas iguales) → centramos en 50.
        out[k] = span === 0 ? 50 : ((v - min) / span) * 100;
      }
    }
    realPorFila.set(etiquetaFila, reales);
    return out;
  });

  return (
    <div className="chart-block">
      {block.title ? <div className="chart-title">{block.title}</div> : null}
      <ResponsiveContainer width="100%" height={300}>
        <RadarChart data={dataNorm}>
          <PolarGrid stroke={gridStroke} />
          <PolarAngleAxis dataKey={xKey} fontSize={12} />
          {/* Dominio fijo 0-100: la normalización ya llevó cada eje a esa escala. */}
          <PolarRadiusAxis domain={[0, 100]} fontSize={10} />
          <Tooltip
            // Mostramos el valor REAL (no el normalizado) leyéndolo del mapa.
            formatter={(_value, name, item) => {
              const fila = realPorFila.get(String(item?.payload?.[xKey] ?? ""));
              const real = fila?.[String(name)];
              return formatearValor(real, block.unit);
            }}
          />
          {/* Misma regla que en barras: con una sola serie la leyenda es redundante
              (el chart-title ya la nombra); solo la mostramos con 2+ series. */}
          {keys.length > 1 ? <Legend /> : null}
          {keys.map((k, i) => (
            <Radar
              key={k}
              name={legibleParaSerie(k, block.title, block.unit)}
              dataKey={k}
              stroke={colors[i % colors.length]}
              fill={colors[i % colors.length]}
              fillOpacity={0.35}
            />
          ))}
        </RadarChart>
      </ResponsiveContainer>
    </div>
  );
}

function TableBlockView({ block }: { block: TableBlock }) {
  const columns =
    block.columns.length > 0
      ? block.columns
      : block.rows[0]
        ? Object.keys(block.rows[0])
        : [];
  return (
    <div className="chart-block">
      {block.title ? <div className="chart-title">{block.title}</div> : null}
      <div className="md-table-wrap">
        <table className="md-table">
          <thead>
            <tr>
              {columns.map((c) => (
                <th key={c}>{c}</th>
              ))}
            </tr>
          </thead>
          <tbody>
            {block.rows.map((row, i) => (
              <tr key={i}>
                {columns.map((c) => (
                  <td key={c}>
                    <ReactMarkdown
                      remarkPlugins={[remarkGfm]}
                      components={MD_CELL_COMPONENTS}
                    >
                      {String(row[c] ?? "")}
                    </ReactMarkdown>
                  </td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}

function ImageBlockView({ block }: { block: ImageBlock }) {
  const { t } = useTranslation();
  const favorites = useFavorites();
  if (!block.foto_url) return null;
  const fav = favorites.includes(block.car_id);
  const favLabel = fav ? t("favorite.remove") : t("favorite.add");
  return (
    <figure className="car-figure">
      <button
        type="button"
        className={`fav-btn${fav ? " active" : ""}`}
        aria-pressed={fav}
        aria-label={favLabel}
        title={favLabel}
        onClick={() => toggleFavorite(block.car_id)}
      >
        <Heart size={16} aria-hidden fill={fav ? "currentColor" : "none"} />
      </button>
      <img src={block.foto_url} alt={block.caption ?? ""} loading="lazy" />
      {block.caption ? <figcaption>{block.caption}</figcaption> : null}
    </figure>
  );
}

function AssistantBlocks({ blocks }: { blocks: Block[] }) {
  return (
    <>
      {blocks.map((b, i) => {
        switch (b.type) {
          case "text":
            return <TextBlockView key={i} block={b} />;
          case "chart":
            return <ChartBlockView key={i} block={b} />;
          case "table":
            return <TableBlockView key={i} block={b} />;
          case "image":
            return <ImageBlockView key={i} block={b} />;
          default:
            return null;
        }
      })}
    </>
  );
}

export default function MessageBubble(props: MessageBubbleProps) {
  const role: Role = props.role;
  const isError = props.isError ?? false;
  const classes = `msg ${role === "user" ? "user" : "ai"}${
    isError ? " error" : ""
  }`;
  return (
    <div className={classes}>
      <div className="msg-content">
        {props.role === "user" ? (
          props.content
        ) : (
          <AssistantBlocks blocks={props.blocks} />
        )}
      </div>
    </div>
  );
}

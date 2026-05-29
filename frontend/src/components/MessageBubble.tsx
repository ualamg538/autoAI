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

const CHART_COLORS = ["#8ab6d6", "#9ac9a3", "#f2b880", "#c8a2d6", "#e0c36a"];

function TextBlockView({ block }: { block: TextBlock }) {
  return (
    <ReactMarkdown
      remarkPlugins={[remarkGfm]}
      components={{
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
  const keys =
    block.keys ?? (firstRow ? Object.keys(firstRow).filter((k) => k !== xKey) : []);

  if (block.variant === "bar") {
    return (
      <div className="chart-block">
        {block.title ? <div className="chart-title">{block.title}</div> : null}
        <ResponsiveContainer width="100%" height={260}>
          <BarChart data={block.data}>
            <CartesianGrid strokeDasharray="3 3" stroke="#eee" />
            <XAxis dataKey={xKey} stroke="#6b6b6b" fontSize={12} />
            <YAxis stroke="#6b6b6b" fontSize={12} />
            <Tooltip />
            <Legend />
            {keys.map((k, i) => (
              <Bar
                key={k}
                dataKey={k}
                fill={CHART_COLORS[i % CHART_COLORS.length]}
                radius={[4, 4, 0, 0]}
              />
            ))}
          </BarChart>
        </ResponsiveContainer>
      </div>
    );
  }

  return (
    <div className="chart-block">
      {block.title ? <div className="chart-title">{block.title}</div> : null}
      <ResponsiveContainer width="100%" height={300}>
        <RadarChart data={block.data}>
          <PolarGrid stroke="#e5e5e5" />
          <PolarAngleAxis dataKey={xKey} fontSize={12} />
          <PolarRadiusAxis fontSize={10} />
          <Tooltip />
          <Legend />
          {keys.map((k, i) => (
            <Radar
              key={k}
              name={k}
              dataKey={k}
              stroke={CHART_COLORS[i % CHART_COLORS.length]}
              fill={CHART_COLORS[i % CHART_COLORS.length]}
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
                  <td key={c}>{String(row[c] ?? "")}</td>
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
  const favorites = useFavorites();
  if (!block.foto_url) return null;
  const fav = favorites.includes(block.car_id);
  return (
    <figure className="car-figure">
      <button
        type="button"
        className={`fav-btn${fav ? " active" : ""}`}
        aria-pressed={fav}
        aria-label={fav ? "Quitar de favoritos" : "Guardar en favoritos"}
        title={fav ? "Quitar de favoritos" : "Guardar en favoritos"}
        onClick={() => toggleFavorite(block.car_id)}
      >
        {fav ? "❤️" : "🤍"}
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

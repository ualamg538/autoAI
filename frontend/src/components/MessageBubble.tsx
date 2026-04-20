import { Fragment, useMemo } from "react";
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

type Role = "user" | "assistant";

interface MessageBubbleProps {
  role: Role;
  content: string;
  isError?: boolean;
}

type ChartType = "bar" | "radar" | "table";

interface ChartSpec {
  type: ChartType;
  title?: string;
  data: Array<Record<string, unknown>>;
  keys?: string[];
  xKey?: string;
}

interface TextSegment {
  kind: "text";
  value: string;
}
interface ChartSegment {
  kind: "chart";
  raw: string;
}
type Segment = TextSegment | ChartSegment;

const CHART_COLORS = ["#8ab6d6", "#9ac9a3", "#f2b880", "#c8a2d6", "#e0c36a"];

function splitSegments(content: string): Segment[] {
  const segments: Segment[] = [];
  const regex = /```chart\s*\n([\s\S]*?)```/g;
  let lastIndex = 0;
  let match: RegExpExecArray | null;

  while ((match = regex.exec(content)) !== null) {
    if (match.index > lastIndex) {
      segments.push({
        kind: "text",
        value: content.slice(lastIndex, match.index),
      });
    }
    segments.push({ kind: "chart", raw: match[1] });
    lastIndex = regex.lastIndex;
  }

  if (lastIndex < content.length) {
    segments.push({ kind: "text", value: content.slice(lastIndex) });
  }
  if (segments.length === 0) {
    segments.push({ kind: "text", value: content });
  }
  return segments;
}

function parseChart(raw: string): ChartSpec | null {
  try {
    const parsed = JSON.parse(raw) as ChartSpec;
    if (
      !parsed ||
      (parsed.type !== "bar" &&
        parsed.type !== "radar" &&
        parsed.type !== "table") ||
      !Array.isArray(parsed.data)
    ) {
      return null;
    }
    return parsed;
  } catch {
    return null;
  }
}

function ChartRenderer({ spec }: { spec: ChartSpec }) {
  const xKey =
    spec.xKey ??
    (spec.data[0] ? Object.keys(spec.data[0])[0] : undefined) ??
    "name";
  const keys =
    spec.keys ??
    (spec.data[0]
      ? Object.keys(spec.data[0]).filter((k) => k !== xKey)
      : []);

  if (spec.type === "table") {
    const columns = spec.data[0] ? Object.keys(spec.data[0]) : [];
    return (
      <div className="chart-block">
        {spec.title ? <div className="chart-title">{spec.title}</div> : null}
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
              {spec.data.map((row, i) => (
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

  if (spec.type === "bar") {
    return (
      <div className="chart-block">
        {spec.title ? <div className="chart-title">{spec.title}</div> : null}
        <ResponsiveContainer width="100%" height={260}>
          <BarChart data={spec.data}>
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

  // radar
  return (
    <div className="chart-block">
      {spec.title ? <div className="chart-title">{spec.title}</div> : null}
      <ResponsiveContainer width="100%" height={300}>
        <RadarChart data={spec.data}>
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

function AssistantContent({ content }: { content: string }) {
  const segments = useMemo(() => splitSegments(content), [content]);

  return (
    <>
      {segments.map((seg, idx) => {
        if (seg.kind === "chart") {
          const spec = parseChart(seg.raw);
          if (!spec) {
            return (
              <div key={idx} className="chart-error">
                No se pudo renderizar el gráfico (JSON inválido).
              </div>
            );
          }
          return <ChartRenderer key={idx} spec={spec} />;
        }
        if (!seg.value.trim()) {
          return <Fragment key={idx} />;
        }
        return (
          <ReactMarkdown
            key={idx}
            remarkPlugins={[remarkGfm]}
            components={{
              table: ({ children }) => (
                <div className="md-table-wrap">
                  <table className="md-table">{children}</table>
                </div>
              ),
            }}
          >
            {seg.value}
          </ReactMarkdown>
        );
      })}
    </>
  );
}

export default function MessageBubble({
  role,
  content,
  isError = false,
}: MessageBubbleProps) {
  const classes = `msg ${role === "user" ? "user" : "ai"}${
    isError ? " error" : ""
  }`;
  return (
    <div className={classes}>
      <div className="msg-content">
        {role === "user" ? (
          content
        ) : (
          <AssistantContent content={content} />
        )}
      </div>
    </div>
  );
}

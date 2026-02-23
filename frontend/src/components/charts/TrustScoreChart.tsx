"use client";

import {
  ResponsiveContainer,
  LineChart,
  Line,
  CartesianGrid,
  XAxis,
  YAxis,
  Tooltip,
  Legend,
  ReferenceLine,
} from "recharts";

interface TrustScoreChartProps {
  data: Array<{ round_id: number; score: number; computed_at: string }>;
}

export default function TrustScoreChart({ data }: TrustScoreChartProps) {
  return (
    <ResponsiveContainer width="100%" height={300}>
      <LineChart data={data} margin={{ top: 5, right: 20, left: 10, bottom: 5 }}>
        <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
        <XAxis
          dataKey="round_id"
          label={{ value: "Round", position: "insideBottomRight", offset: -5 }}
          tick={{ fontSize: 12 }}
        />
        <YAxis
          domain={[0, 1]}
          tick={{ fontSize: 12 }}
          label={{ value: "Score", angle: -90, position: "insideLeft" }}
        />
        <Tooltip
          formatter={(value: number) => [value.toFixed(4), "Trust Score"]}
          labelFormatter={(label) => `Round ${label}`}
          contentStyle={{
            borderRadius: "8px",
            border: "1px solid #e5e7eb",
            boxShadow: "0 2px 8px rgba(0,0,0,0.1)",
          }}
        />
        <Legend />
        <ReferenceLine
          y={0.5}
          stroke="#ef4444"
          strokeDasharray="3 3"
          label={{ value: "Flag Threshold", position: "right", fill: "#ef4444", fontSize: 12 }}
        />
        <Line
          type="monotone"
          dataKey="score"
          stroke="#10b981"
          strokeWidth={2}
          dot={true}
          name="Trust Score"
          activeDot={{ r: 6 }}
        />
      </LineChart>
    </ResponsiveContainer>
  );
}

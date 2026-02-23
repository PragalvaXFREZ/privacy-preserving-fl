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

interface AUCChartProps {
  data: Array<{ round_number: number; global_auc: number }>;
}

export default function AUCChart({ data }: AUCChartProps) {
  return (
    <ResponsiveContainer width="100%" height={300}>
      <LineChart data={data} margin={{ top: 5, right: 20, left: 10, bottom: 5 }}>
        <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
        <XAxis
          dataKey="round_number"
          label={{ value: "Round", position: "insideBottomRight", offset: -5 }}
          tick={{ fontSize: 12 }}
        />
        <YAxis
          domain={[0, 1]}
          tick={{ fontSize: 12 }}
          label={{ value: "AUC", angle: -90, position: "insideLeft" }}
        />
        <Tooltip
          formatter={(value: number) => [value.toFixed(4), "Global AUC"]}
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
          label={{ value: "Random", position: "right", fill: "#ef4444", fontSize: 12 }}
        />
        <Line
          type="monotone"
          dataKey="global_auc"
          stroke="#3b82f6"
          strokeWidth={2}
          dot={true}
          name="Global AUC"
          activeDot={{ r: 6 }}
        />
      </LineChart>
    </ResponsiveContainer>
  );
}

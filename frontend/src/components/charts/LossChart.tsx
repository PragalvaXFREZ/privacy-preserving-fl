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
} from "recharts";

interface LossChartProps {
  data: Array<{ round_number: number; global_loss: number }>;
}

export default function LossChart({ data }: LossChartProps) {
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
          tick={{ fontSize: 12 }}
          label={{ value: "Loss", angle: -90, position: "insideLeft" }}
        />
        <Tooltip
          formatter={(value: number) => [value.toFixed(4), "Global Loss"]}
          labelFormatter={(label) => `Round ${label}`}
          contentStyle={{
            borderRadius: "8px",
            border: "1px solid #e5e7eb",
            boxShadow: "0 2px 8px rgba(0,0,0,0.1)",
          }}
        />
        <Legend />
        <Line
          type="monotone"
          dataKey="global_loss"
          stroke="#f97316"
          strokeWidth={2}
          dot={true}
          name="Global Loss"
          activeDot={{ r: 6 }}
        />
      </LineChart>
    </ResponsiveContainer>
  );
}

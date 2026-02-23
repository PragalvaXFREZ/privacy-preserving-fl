"use client";

import {
  ResponsiveContainer,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  Cell,
} from "recharts";
import type { InferenceResult } from "@/lib/types";
import { cn } from "@/lib/utils";

interface PredictionResultProps {
  result: InferenceResult;
}

export default function PredictionResult({ result }: PredictionResultProps) {
  const predictions = Object.entries(result.predictions)
    .map(([name, probability]) => ({ name, probability }))
    .sort((a, b) => b.probability - a.probability);

  const topFinding = result.top_finding;
  const confidence = result.confidence;

  const confidenceColor =
    confidence > 0.7
      ? "text-red-600"
      : confidence > 0.4
      ? "text-orange-500"
      : "text-green-600";

  const confidenceBg =
    confidence > 0.7
      ? "bg-red-50"
      : confidence > 0.4
      ? "bg-orange-50"
      : "bg-green-50";

  const getBarColor = (probability: number): string => {
    if (probability > 0.5) return "#ef4444";
    if (probability > 0.3) return "#f97316";
    return "#22c55e";
  };

  return (
    <div className="space-y-6">
      <div className={cn("rounded-lg p-4 text-center", confidenceBg)}>
        <p className="text-sm font-medium text-gray-500 mb-1">Top Finding</p>
        <p className="text-xl font-bold text-gray-900">{topFinding}</p>
        <p className={cn("text-3xl font-bold mt-1", confidenceColor)}>
          {(confidence * 100).toFixed(1)}%
        </p>
      </div>

      {predictions.length > 0 && (
        <div>
          <p className="text-sm font-medium text-gray-700 mb-2">
            All Predictions
          </p>
          <ResponsiveContainer width="100%" height={Math.max(predictions.length * 40, 200)}>
            <BarChart
              data={predictions}
              layout="vertical"
              margin={{ top: 5, right: 20, left: 10, bottom: 5 }}
            >
              <XAxis
                type="number"
                domain={[0, 1]}
                tick={{ fontSize: 12 }}
                tickFormatter={(v) => `${(v * 100).toFixed(0)}%`}
              />
              <YAxis
                type="category"
                dataKey="name"
                width={140}
                tick={{ fontSize: 11 }}
              />
              <Tooltip
                formatter={(value: number) => [
                  `${(value * 100).toFixed(1)}%`,
                  "Probability",
                ]}
                contentStyle={{
                  borderRadius: "8px",
                  border: "1px solid #e5e7eb",
                  boxShadow: "0 2px 8px rgba(0,0,0,0.1)",
                }}
              />
              <Bar dataKey="probability" radius={[0, 4, 4, 0]}>
                {predictions.map((entry, index) => (
                  <Cell
                    key={`cell-${index}`}
                    fill={getBarColor(entry.probability)}
                  />
                ))}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        </div>
      )}

      <div className="flex items-center justify-between text-xs text-gray-500 border-t pt-3">
        <span>Model: {result.model_version}</span>
        <span>Inference: {result.inference_time_ms.toFixed(0)}ms</span>
      </div>
    </div>
  );
}

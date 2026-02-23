"use client";

import { useEffect, useState } from "react";
import { uploadXray, getInferenceHistory } from "@/lib/api";
import type { InferenceResult } from "@/lib/types";
import { formatDate } from "@/lib/utils";
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import XrayUploader from "@/components/inference/XrayUploader";
import PredictionResult from "@/components/inference/PredictionResult";

export default function InferencePage() {
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [prediction, setPrediction] = useState<InferenceResult | null>(null);
  const [loading, setLoading] = useState(false);
  const [history, setHistory] = useState<InferenceResult[]>([]);
  const [historyLoading, setHistoryLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    async function fetchHistory() {
      try {
        const data = await getInferenceHistory();
        setHistory(data);
      } catch (err) {
        console.error("Failed to fetch inference history:", err);
      } finally {
        setHistoryLoading(false);
      }
    }
    fetchHistory();
  }, []);

  const handleUpload = async (file: File) => {
    setSelectedFile(file);
    setError(null);
    setLoading(true);
    setPrediction(null);

    try {
      const result = await uploadXray(file);
      setPrediction(result);
      setHistory((prev) => [result, ...prev]);
    } catch (err) {
      const message =
        err instanceof Error ? err.message : "Inference failed";
      setError(message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="space-y-6">
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <Card>
          <CardHeader>
            <CardTitle className="text-lg">Upload X-ray</CardTitle>
          </CardHeader>
          <CardContent>
            <XrayUploader onUpload={handleUpload} loading={loading} />
            {error && (
              <p className="mt-3 text-sm text-red-600 bg-red-50 rounded-md p-3">
                {error}
              </p>
            )}
          </CardContent>
        </Card>

        {prediction && (
          <Card>
            <CardHeader>
              <CardTitle className="text-lg">Prediction Results</CardTitle>
            </CardHeader>
            <CardContent>
              <PredictionResult result={prediction} />
            </CardContent>
          </Card>
        )}
      </div>

      <Card>
        <CardHeader>
          <CardTitle className="text-lg">Inference History</CardTitle>
        </CardHeader>
        <CardContent>
          {historyLoading ? (
            <div className="space-y-3">
              {[...Array(3)].map((_, i) => (
                <div key={i} className="h-12 animate-pulse rounded bg-gray-200" />
              ))}
            </div>
          ) : history.length > 0 ? (
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b text-left text-gray-500">
                    <th className="pb-3 font-medium">Image</th>
                    <th className="pb-3 font-medium">Top Finding</th>
                    <th className="pb-3 font-medium">Confidence</th>
                    <th className="pb-3 font-medium">Inference Time</th>
                    <th className="pb-3 font-medium">Model Version</th>
                    <th className="pb-3 font-medium">Date</th>
                  </tr>
                </thead>
                <tbody>
                  {history.map((item) => (
                    <tr
                      key={item.id}
                      className="border-b last:border-0 hover:bg-gray-50"
                    >
                      <td className="py-3 font-mono text-xs">
                        {item.image_filename}
                      </td>
                      <td className="py-3 font-medium">{item.top_finding}</td>
                      <td className="py-3">
                        <Badge
                          variant={
                            item.confidence > 0.7
                              ? "destructive"
                              : item.confidence > 0.4
                              ? "default"
                              : "online"
                          }
                        >
                          {(item.confidence * 100).toFixed(1)}%
                        </Badge>
                      </td>
                      <td className="py-3">{item.inference_time_ms.toFixed(0)}ms</td>
                      <td className="py-3">{item.model_version}</td>
                      <td className="py-3">{formatDate(item.created_at)}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          ) : (
            <p className="text-sm text-gray-500 text-center py-8">
              No inference history available yet. Upload an X-ray to get started.
            </p>
          )}
        </CardContent>
      </Card>
    </div>
  );
}

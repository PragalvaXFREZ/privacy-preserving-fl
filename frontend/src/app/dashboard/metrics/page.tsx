"use client";

import { useEffect, useState } from "react";
import { getAUCHistory, getLossHistory, getAggregationStats } from "@/lib/api";
import type {
  AUCHistoryItem,
  LossHistoryItem,
  AggregationStats,
} from "@/lib/types";
import { formatNumber } from "@/lib/utils";
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import AUCChart from "@/components/charts/AUCChart";
import LossChart from "@/components/charts/LossChart";
import { Lock, ShieldCheck } from "lucide-react";

export default function MetricsPage() {
  const [aucHistory, setAucHistory] = useState<AUCHistoryItem[]>([]);
  const [lossHistory, setLossHistory] = useState<LossHistoryItem[]>([]);
  const [aggStats, setAggStats] = useState<AggregationStats[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function fetchData() {
      try {
        const [auc, loss, agg] = await Promise.all([
          getAUCHistory(),
          getLossHistory(),
          getAggregationStats(),
        ]);
        setAucHistory(auc);
        setLossHistory(loss);
        setAggStats(agg);
      } catch (err) {
        console.error("Failed to fetch metrics:", err);
      } finally {
        setLoading(false);
      }
    }
    fetchData();
  }, []);

  if (loading) {
    return (
      <div className="space-y-6">
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <div className="h-80 animate-pulse rounded-lg bg-gray-200" />
          <div className="h-80 animate-pulse rounded-lg bg-gray-200" />
        </div>
        <div className="h-64 animate-pulse rounded-lg bg-gray-200" />
        <div className="h-48 animate-pulse rounded-lg bg-gray-200" />
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <Card>
          <CardHeader>
            <CardTitle className="text-lg">AUC History</CardTitle>
          </CardHeader>
          <CardContent>
            {aucHistory.length > 0 ? (
              <AUCChart data={aucHistory} />
            ) : (
              <p className="text-sm text-gray-500 text-center py-8">
                No AUC history data available.
              </p>
            )}
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle className="text-lg">Loss History</CardTitle>
          </CardHeader>
          <CardContent>
            {lossHistory.length > 0 ? (
              <LossChart data={lossHistory} />
            ) : (
              <p className="text-sm text-gray-500 text-center py-8">
                No loss history data available.
              </p>
            )}
          </CardContent>
        </Card>
      </div>

      <Card>
        <CardHeader>
          <CardTitle className="text-lg">Aggregation Statistics</CardTitle>
        </CardHeader>
        <CardContent>
          {aggStats.length > 0 ? (
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b text-left text-gray-500">
                    <th className="pb-3 font-medium">Round</th>
                    <th className="pb-3 font-medium">Method</th>
                    <th className="pb-3 font-medium">Poisoned Detected</th>
                    <th className="pb-3 font-medium">Agg. Time (ms)</th>
                    <th className="pb-3 font-medium">Encryption Overhead (ms)</th>
                  </tr>
                </thead>
                <tbody>
                  {aggStats.map((stat, idx) => (
                    <tr
                      key={idx}
                      className="border-b last:border-0 hover:bg-gray-50"
                    >
                      <td className="py-3 font-medium">{stat.round_number}</td>
                      <td className="py-3">
                        <Badge variant="secondary">{stat.aggregation_method}</Badge>
                      </td>
                      <td className="py-3">{stat.poisoned_clients_detected}</td>
                      <td className="py-3">
                        {formatNumber(stat.aggregation_time_ms, 1)}
                      </td>
                      <td className="py-3">
                        {formatNumber(stat.encryption_overhead_ms, 1)}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          ) : (
            <p className="text-sm text-gray-500 text-center py-8">
              No aggregation statistics available.
            </p>
          )}
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle className="text-lg flex items-center gap-2">
            <ShieldCheck className="h-5 w-5 text-green-600" />
            Privacy Parameters
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            <div className="flex items-center gap-3 p-4 rounded-lg bg-green-50">
              <Lock className="h-8 w-8 text-green-600" />
              <div>
                <p className="text-sm font-medium text-gray-500">
                  Encryption Coverage
                </p>
                <p className="text-2xl font-bold text-gray-900">50%</p>
              </div>
            </div>
            <div className="flex items-center gap-3 p-4 rounded-lg bg-blue-50">
              <ShieldCheck className="h-8 w-8 text-blue-600" />
              <div>
                <p className="text-sm font-medium text-gray-500">
                  DP Epsilon
                </p>
                <p className="text-2xl font-bold text-gray-900">1.0</p>
              </div>
            </div>
            <div className="flex items-center gap-3 p-4 rounded-lg bg-purple-50">
              <ShieldCheck className="h-8 w-8 text-purple-600" />
              <div>
                <p className="text-sm font-medium text-gray-500">
                  DP Delta
                </p>
                <p className="text-2xl font-bold text-gray-900">1e-5</p>
              </div>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}

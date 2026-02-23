"use client";

import { useEffect, useState } from "react";
import {
  Activity,
  Server,
  TrendingUp,
  AlertTriangle,
} from "lucide-react";
import { getOverview, getAUCHistory, getTrainingRounds } from "@/lib/api";
import type {
  OverviewMetrics,
  AUCHistoryItem,
  TrainingRound,
} from "@/lib/types";
import { formatDate, formatNumber, formatDuration } from "@/lib/utils";
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import AUCChart from "@/components/charts/AUCChart";

const statusBadgeVariant: Record<string, "secondary" | "training" | "online" | "destructive"> = {
  pending: "secondary",
  in_progress: "training",
  aggregating: "training",
  completed: "online",
  failed: "destructive",
};

export default function DashboardOverview() {
  const [overview, setOverview] = useState<OverviewMetrics | null>(null);
  const [aucHistory, setAucHistory] = useState<AUCHistoryItem[]>([]);
  const [recentRounds, setRecentRounds] = useState<TrainingRound[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function fetchData() {
      try {
        const [overviewData, aucData, roundsData] = await Promise.all([
          getOverview(),
          getAUCHistory(),
          getTrainingRounds(0, 5),
        ]);
        setOverview(overviewData);
        setAucHistory(aucData);
        setRecentRounds(roundsData);
      } catch (err) {
        console.error("Failed to fetch dashboard data:", err);
      } finally {
        setLoading(false);
      }
    }
    fetchData();
  }, []);

  if (loading) {
    return (
      <div className="space-y-6">
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          {[...Array(4)].map((_, i) => (
            <div key={i} className="h-32 animate-pulse rounded-lg bg-gray-200" />
          ))}
        </div>
        <div className="h-80 animate-pulse rounded-lg bg-gray-200" />
        <div className="h-64 animate-pulse rounded-lg bg-gray-200" />
      </div>
    );
  }

  const statCards = [
    {
      title: "Total Rounds",
      value: overview?.total_rounds ?? 0,
      icon: Activity,
      iconBg: "bg-blue-50",
      iconColor: "text-blue-600",
    },
    {
      title: "Active Clients",
      value: overview?.active_clients ?? 0,
      icon: Server,
      iconBg: "bg-green-50",
      iconColor: "text-green-600",
    },
    {
      title: "Latest AUC",
      value:
        overview?.latest_auc !== undefined && overview?.latest_auc !== null
          ? `${(overview.latest_auc * 100).toFixed(1)}%`
          : "--",
      icon: TrendingUp,
      iconBg: "bg-purple-50",
      iconColor: "text-purple-600",
    },
    {
      title: "Flagged Clients",
      value: overview?.flagged_clients ?? 0,
      icon: AlertTriangle,
      iconBg: "bg-amber-50",
      iconColor: "text-amber-600",
    },
  ];

  return (
    <div className="space-y-6">
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        {statCards.map((stat) => {
          const Icon = stat.icon;
          return (
            <Card key={stat.title}>
              <CardContent className="p-6">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-sm font-medium text-gray-500">
                      {stat.title}
                    </p>
                    <p className="text-3xl font-bold text-gray-900 mt-1">
                      {stat.value}
                    </p>
                  </div>
                  <div
                    className={`flex h-12 w-12 items-center justify-center rounded-lg ${stat.iconBg}`}
                  >
                    <Icon className={`h-6 w-6 ${stat.iconColor}`} />
                  </div>
                </div>
              </CardContent>
            </Card>
          );
        })}
      </div>

      <Card>
        <CardHeader>
          <CardTitle className="text-lg">AUC Trend</CardTitle>
        </CardHeader>
        <CardContent>
          {aucHistory.length > 0 ? (
            <AUCChart data={aucHistory} />
          ) : (
            <p className="text-sm text-gray-500 text-center py-8">
              No AUC history data available yet.
            </p>
          )}
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle className="text-lg">Recent Training Rounds</CardTitle>
        </CardHeader>
        <CardContent>
          {recentRounds.length > 0 ? (
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b text-left text-gray-500">
                    <th className="pb-3 font-medium">Round #</th>
                    <th className="pb-3 font-medium">Status</th>
                    <th className="pb-3 font-medium">Clients</th>
                    <th className="pb-3 font-medium">Global AUC</th>
                    <th className="pb-3 font-medium">Global Loss</th>
                    <th className="pb-3 font-medium">Started</th>
                    <th className="pb-3 font-medium">Duration</th>
                  </tr>
                </thead>
                <tbody>
                  {recentRounds.map((round) => (
                    <tr
                      key={round.id}
                      className="border-b last:border-0 hover:bg-gray-50"
                    >
                      <td className="py-3 font-medium">{round.round_number}</td>
                      <td className="py-3">
                        <Badge variant={statusBadgeVariant[round.status] || "secondary"}>
                          {round.status.replace("_", " ")}
                        </Badge>
                      </td>
                      <td className="py-3">{round.num_clients}</td>
                      <td className="py-3">{formatNumber(round.global_auc)}</td>
                      <td className="py-3">{formatNumber(round.global_loss)}</td>
                      <td className="py-3">{formatDate(round.started_at)}</td>
                      <td className="py-3">
                        {formatDuration(round.started_at, round.completed_at)}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          ) : (
            <p className="text-sm text-gray-500 text-center py-8">
              No training rounds available yet.
            </p>
          )}
        </CardContent>
      </Card>
    </div>
  );
}

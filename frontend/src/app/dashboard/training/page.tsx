"use client";

import { useEffect, useState } from "react";
import { getTrainingRounds, getRoundUpdates, getCurrentRound } from "@/lib/api";
import type { TrainingRound, ClientUpdate } from "@/lib/types";
import { formatDate, formatNumber, formatDuration } from "@/lib/utils";
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Activity, ChevronDown, ChevronRight } from "lucide-react";

const statusBadgeVariant: Record<string, "secondary" | "training" | "online" | "destructive"> = {
  pending: "secondary",
  in_progress: "training",
  aggregating: "training",
  completed: "online",
  failed: "destructive",
};

export default function TrainingPage() {
  const [rounds, setRounds] = useState<TrainingRound[]>([]);
  const [currentRound, setCurrentRound] = useState<TrainingRound | null>(null);
  const [loading, setLoading] = useState(true);
  const [expandedRound, setExpandedRound] = useState<number | null>(null);
  const [roundUpdates, setRoundUpdates] = useState<Record<number, ClientUpdate[]>>({});
  const [updatesLoading, setUpdatesLoading] = useState<number | null>(null);

  useEffect(() => {
    async function fetchData() {
      try {
        const [roundsData, current] = await Promise.all([
          getTrainingRounds(),
          getCurrentRound(),
        ]);
        setRounds(roundsData);
        setCurrentRound(current);
      } catch (err) {
        console.error("Failed to fetch training rounds:", err);
      } finally {
        setLoading(false);
      }
    }
    fetchData();
  }, []);

  const handleRowClick = async (round: TrainingRound) => {
    if (expandedRound === round.id) {
      setExpandedRound(null);
      return;
    }

    setExpandedRound(round.id);

    if (!roundUpdates[round.id]) {
      setUpdatesLoading(round.id);
      try {
        const updates = await getRoundUpdates(round.id);
        setRoundUpdates((prev) => ({ ...prev, [round.id]: updates }));
      } catch (err) {
        console.error("Failed to fetch round updates:", err);
      } finally {
        setUpdatesLoading(null);
      }
    }
  };

  if (loading) {
    return (
      <div className="space-y-4">
        <div className="h-24 animate-pulse rounded-lg bg-gray-200" />
        <div className="h-96 animate-pulse rounded-lg bg-gray-200" />
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {currentRound && currentRound.status === "in_progress" && (
        <Card className="border-blue-200 bg-blue-50">
          <CardContent className="p-4">
            <div className="flex items-center gap-3">
              <div className="flex h-10 w-10 items-center justify-center rounded-full bg-blue-100">
                <Activity className="h-5 w-5 text-blue-600 animate-pulse" />
              </div>
              <div>
                <p className="font-semibold text-blue-900">
                  Round {currentRound.round_number} In Progress
                </p>
                <p className="text-sm text-blue-700">
                  {currentRound.num_clients} clients participating -- Started{" "}
                  {formatDate(currentRound.started_at)}
                </p>
              </div>
            </div>
          </CardContent>
        </Card>
      )}

      <Card>
        <CardHeader>
          <CardTitle className="text-lg">All Training Rounds</CardTitle>
        </CardHeader>
        <CardContent>
          {rounds.length > 0 ? (
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b text-left text-gray-500">
                    <th className="pb-3 pr-2 font-medium w-8"></th>
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
                  {rounds.map((round) => (
                    <>
                      <tr
                        key={round.id}
                        className="border-b hover:bg-gray-50 cursor-pointer"
                        onClick={() => handleRowClick(round)}
                      >
                        <td className="py-3 pr-2">
                          {expandedRound === round.id ? (
                            <ChevronDown className="h-4 w-4 text-gray-400" />
                          ) : (
                            <ChevronRight className="h-4 w-4 text-gray-400" />
                          )}
                        </td>
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
                      {expandedRound === round.id && (
                        <tr key={`${round.id}-expanded`}>
                          <td colSpan={8} className="bg-gray-50 p-4">
                            {updatesLoading === round.id ? (
                              <div className="flex items-center justify-center py-4">
                                <div className="h-5 w-5 animate-spin rounded-full border-2 border-blue-600 border-t-transparent" />
                                <span className="ml-2 text-sm text-gray-500">
                                  Loading client updates...
                                </span>
                              </div>
                            ) : roundUpdates[round.id]?.length ? (
                              <div>
                                <p className="text-sm font-semibold text-gray-700 mb-2">
                                  Client Updates
                                </p>
                                <table className="w-full text-xs">
                                  <thead>
                                    <tr className="border-b text-left text-gray-500">
                                      <th className="pb-2 font-medium">Client ID</th>
                                      <th className="pb-2 font-medium">Local AUC</th>
                                      <th className="pb-2 font-medium">Local Loss</th>
                                      <th className="pb-2 font-medium">Samples</th>
                                      <th className="pb-2 font-medium">Euclidean Dist.</th>
                                      <th className="pb-2 font-medium">Encryption</th>
                                      <th className="pb-2 font-medium">Submitted</th>
                                    </tr>
                                  </thead>
                                  <tbody>
                                    {roundUpdates[round.id].map((update) => (
                                      <tr
                                        key={update.id}
                                        className="border-b last:border-0"
                                      >
                                        <td className="py-2 font-mono">
                                          {update.client_id}
                                        </td>
                                        <td className="py-2">
                                          {formatNumber(update.local_auc)}
                                        </td>
                                        <td className="py-2">
                                          {formatNumber(update.local_loss)}
                                        </td>
                                        <td className="py-2">
                                          {update.num_samples.toLocaleString()}
                                        </td>
                                        <td className="py-2">
                                          {formatNumber(update.euclidean_distance)}
                                        </td>
                                        <td className="py-2">
                                          <Badge
                                            variant={
                                              update.encryption_status === "encrypted"
                                                ? "online"
                                                : "secondary"
                                            }
                                          >
                                            {update.encryption_status}
                                          </Badge>
                                        </td>
                                        <td className="py-2">
                                          {formatDate(update.submitted_at)}
                                        </td>
                                      </tr>
                                    ))}
                                  </tbody>
                                </table>
                              </div>
                            ) : (
                              <p className="text-sm text-gray-500 text-center py-2">
                                No client updates for this round.
                              </p>
                            )}
                          </td>
                        </tr>
                      )}
                    </>
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

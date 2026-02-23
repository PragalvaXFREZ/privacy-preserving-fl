"use client";

import { useState } from "react";
import { ChevronDown, ChevronRight } from "lucide-react";
import { getRoundUpdates } from "@/lib/api";
import type { TrainingRound, ClientUpdate } from "@/lib/types";
import { formatDate, formatNumber, formatDuration } from "@/lib/utils";
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";

const statusBadgeVariant: Record<string, "secondary" | "training" | "online" | "destructive"> = {
  pending: "secondary",
  in_progress: "training",
  aggregating: "training",
  completed: "online",
  failed: "destructive",
};

interface RoundCardProps {
  round: TrainingRound;
}

export default function RoundCard({ round }: RoundCardProps) {
  const [expanded, setExpanded] = useState(false);
  const [updates, setUpdates] = useState<ClientUpdate[]>([]);
  const [loading, setLoading] = useState(false);

  const handleToggle = async () => {
    if (expanded) {
      setExpanded(false);
      return;
    }

    setExpanded(true);

    if (updates.length === 0) {
      setLoading(true);
      try {
        const data = await getRoundUpdates(round.id);
        setUpdates(data);
      } catch (err) {
        console.error("Failed to fetch round updates:", err);
      } finally {
        setLoading(false);
      }
    }
  };

  return (
    <Card>
      <CardHeader
        className="cursor-pointer hover:bg-gray-50 transition-colors"
        onClick={handleToggle}
      >
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            {expanded ? (
              <ChevronDown className="h-5 w-5 text-gray-400" />
            ) : (
              <ChevronRight className="h-5 w-5 text-gray-400" />
            )}
            <CardTitle className="text-base">
              Round {round.round_number}
            </CardTitle>
            <Badge variant={statusBadgeVariant[round.status] || "secondary"}>
              {round.status.replace("_", " ")}
            </Badge>
          </div>
          <div className="flex items-center gap-6 text-sm text-gray-500">
            <span>{round.num_clients} clients</span>
            <span>AUC: {formatNumber(round.global_auc)}</span>
            <span>Loss: {formatNumber(round.global_loss)}</span>
            <span>{formatDuration(round.started_at, round.completed_at)}</span>
          </div>
        </div>
      </CardHeader>

      {expanded && (
        <CardContent>
          <div className="border-t pt-4">
            <p className="text-sm font-medium text-gray-700 mb-2">
              Round Details
            </p>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-4 text-sm">
              <div>
                <p className="text-gray-500">Started</p>
                <p className="font-medium">{formatDate(round.started_at)}</p>
              </div>
              <div>
                <p className="text-gray-500">Completed</p>
                <p className="font-medium">
                  {round.completed_at ? formatDate(round.completed_at) : "--"}
                </p>
              </div>
              <div>
                <p className="text-gray-500">Job ID</p>
                <p className="font-medium font-mono text-xs">{round.job_id}</p>
              </div>
              <div>
                <p className="text-gray-500">Duration</p>
                <p className="font-medium">
                  {formatDuration(round.started_at, round.completed_at)}
                </p>
              </div>
            </div>

            <p className="text-sm font-medium text-gray-700 mb-2">
              Client Updates
            </p>
            {loading ? (
              <div className="flex items-center justify-center py-4">
                <div className="h-5 w-5 animate-spin rounded-full border-2 border-blue-600 border-t-transparent" />
                <span className="ml-2 text-sm text-gray-500">Loading...</span>
              </div>
            ) : updates.length > 0 ? (
              <div className="overflow-x-auto">
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
                    {updates.map((update) => (
                      <tr key={update.id} className="border-b last:border-0">
                        <td className="py-2 font-mono">{update.client_id}</td>
                        <td className="py-2">{formatNumber(update.local_auc)}</td>
                        <td className="py-2">{formatNumber(update.local_loss)}</td>
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
                        <td className="py-2">{formatDate(update.submitted_at)}</td>
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
          </div>
        </CardContent>
      )}
    </Card>
  );
}

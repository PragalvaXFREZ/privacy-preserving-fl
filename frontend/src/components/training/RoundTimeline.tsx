"use client";

import type { TrainingRound } from "@/lib/types";
import { formatNumber, formatDate, formatDuration } from "@/lib/utils";
import { cn } from "@/lib/utils";
import { Badge } from "@/components/ui/badge";

const statusBadgeVariant: Record<string, "secondary" | "training" | "online" | "destructive"> = {
  pending: "secondary",
  in_progress: "training",
  aggregating: "training",
  completed: "online",
  failed: "destructive",
};

const statusDotColor: Record<string, string> = {
  pending: "bg-gray-400",
  in_progress: "bg-blue-500 animate-pulse",
  aggregating: "bg-blue-500 animate-pulse",
  completed: "bg-green-500",
  failed: "bg-red-500",
};

interface RoundTimelineProps {
  rounds: TrainingRound[];
}

export default function RoundTimeline({ rounds }: RoundTimelineProps) {
  const sortedRounds = [...rounds].sort(
    (a, b) => b.round_number - a.round_number
  );

  if (sortedRounds.length === 0) {
    return (
      <p className="text-sm text-gray-500 text-center py-8">
        No training rounds to display.
      </p>
    );
  }

  return (
    <div className="relative">
      <div className="absolute left-4 top-0 bottom-0 w-0.5 bg-gray-200" />
      <ul className="space-y-6">
        {sortedRounds.map((round) => (
          <li key={round.id} className="relative flex gap-4 pl-10">
            <div
              className={cn(
                "absolute left-2.5 top-1.5 h-3 w-3 rounded-full ring-2 ring-white",
                statusDotColor[round.status] || "bg-gray-400"
              )}
            />
            <div className="flex-1 min-w-0">
              <div className="flex items-center gap-3 mb-1">
                <span className="text-sm font-semibold text-gray-900">
                  Round {round.round_number}
                </span>
                <Badge variant={statusBadgeVariant[round.status] || "secondary"}>
                  {round.status.replace("_", " ")}
                </Badge>
              </div>
              <div className="flex flex-wrap items-center gap-4 text-xs text-gray-500">
                <span>AUC: {formatNumber(round.global_auc)}</span>
                <span>Loss: {formatNumber(round.global_loss)}</span>
                <span>{round.num_clients} clients</span>
                <span>
                  {formatDuration(round.started_at, round.completed_at)}
                </span>
                <span>{formatDate(round.started_at)}</span>
              </div>
            </div>
          </li>
        ))}
      </ul>
    </div>
  );
}

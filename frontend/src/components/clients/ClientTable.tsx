"use client";

import type { Client } from "@/lib/types";
import { cn, timeAgo } from "@/lib/utils";
import { Badge } from "@/components/ui/badge";
import TrustBadge from "./TrustBadge";

const statusVariant: Record<string, "online" | "offline" | "training" | "destructive"> = {
  online: "online",
  offline: "offline",
  training: "training",
  error: "destructive",
};

interface ClientTableProps {
  clients: Client[];
  onClientClick?: (id: number) => void;
}

export default function ClientTable({ clients, onClientClick }: ClientTableProps) {
  if (clients.length === 0) {
    return (
      <p className="text-sm text-gray-500 text-center py-8">
        No client nodes registered yet.
      </p>
    );
  }

  return (
    <div className="overflow-x-auto">
      <table className="w-full text-sm">
        <thead>
          <tr className="border-b text-left text-gray-500">
            <th className="pb-3 font-medium">Name</th>
            <th className="pb-3 font-medium">Client ID</th>
            <th className="pb-3 font-medium">Status</th>
            <th className="pb-3 font-medium">Data Profile</th>
            <th className="pb-3 font-medium">Trust Score</th>
            <th className="pb-3 font-medium">Last Heartbeat</th>
          </tr>
        </thead>
        <tbody>
          {clients.map((client) => {
            const trustScore = client.trust_score ?? 0;
            const barColor =
              trustScore >= 0.8
                ? "bg-green-500"
                : trustScore >= 0.5
                ? "bg-yellow-500"
                : "bg-red-500";

            return (
              <tr
                key={client.id}
                className={cn(
                  "border-b last:border-0 hover:bg-gray-50 transition-colors",
                  onClientClick && "cursor-pointer"
                )}
                onClick={() => onClientClick?.(client.id)}
              >
                <td className="py-3 font-medium">{client.name}</td>
                <td className="py-3 font-mono text-xs text-gray-600">
                  {client.client_id}
                </td>
                <td className="py-3">
                  <Badge variant={statusVariant[client.status] || "secondary"}>
                    {client.status}
                  </Badge>
                </td>
                <td className="py-3 text-gray-600">{client.data_profile}</td>
                <td className="py-3">
                  <div className="flex items-center gap-3">
                    <div className="w-24 h-2 bg-gray-200 rounded-full overflow-hidden">
                      <div
                        className={cn("h-full rounded-full transition-all", barColor)}
                        style={{ width: `${Math.min(trustScore * 100, 100)}%` }}
                      />
                    </div>
                    <TrustBadge
                      score={trustScore}
                      isFlagged={client.is_flagged}
                    />
                  </div>
                </td>
                <td className="py-3 text-gray-500">
                  {client.last_heartbeat ? timeAgo(client.last_heartbeat) : "--"}
                </td>
              </tr>
            );
          })}
        </tbody>
      </table>
    </div>
  );
}

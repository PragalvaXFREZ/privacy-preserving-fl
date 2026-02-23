import { cn } from "@/lib/utils";

interface TrustBadgeProps {
  score: number;
  isFlagged?: boolean;
}

export default function TrustBadge({ score, isFlagged }: TrustBadgeProps) {
  const dotColor =
    score >= 0.8
      ? "bg-green-500"
      : score >= 0.5
      ? "bg-yellow-500"
      : "bg-red-500";

  return (
    <div className="flex items-center gap-2">
      <span
        className={cn("inline-block h-2.5 w-2.5 rounded-full", dotColor)}
      />
      <span className="text-sm font-medium text-gray-700">
        {score.toFixed(2)}
      </span>
      {isFlagged && (
        <span className="inline-flex items-center rounded-full bg-red-100 px-2 py-0.5 text-xs font-semibold text-red-800">
          FLAGGED
        </span>
      )}
    </div>
  );
}

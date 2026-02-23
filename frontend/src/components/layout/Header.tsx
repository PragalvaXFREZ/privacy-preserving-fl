"use client";

import { usePathname } from "next/navigation";

const titleMap: Record<string, string> = {
  "/dashboard": "Overview",
  "/dashboard/training": "Training Rounds",
  "/dashboard/clients": "Client Nodes",
  "/dashboard/metrics": "Metrics & Analytics",
  "/dashboard/inference": "X-ray Inference",
};

export default function Header() {
  const pathname = usePathname();
  const title = titleMap[pathname] || "Dashboard";

  return (
    <header className="bg-white border-b px-6 py-4">
      <h1 className="text-2xl font-bold text-gray-900">{title}</h1>
    </header>
  );
}

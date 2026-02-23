"use client";

import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import {
  Shield,
  LayoutDashboard,
  Activity,
  Server,
  BarChart3,
  Scan,
  LogOut,
} from "lucide-react";
import { removeToken } from "@/lib/auth";
import { cn } from "@/lib/utils";

const navItems = [
  { label: "Overview", href: "/dashboard", icon: LayoutDashboard },
  { label: "Training", href: "/dashboard/training", icon: Activity },
  { label: "Clients", href: "/dashboard/clients", icon: Server },
  { label: "Metrics", href: "/dashboard/metrics", icon: BarChart3 },
  { label: "Inference", href: "/dashboard/inference", icon: Scan },
];

export default function Sidebar() {
  const pathname = usePathname();
  const router = useRouter();

  const handleLogout = () => {
    removeToken();
    router.push("/login");
  };

  return (
    <aside className="bg-slate-900 text-white w-64 min-h-screen fixed left-0 top-0 flex flex-col">
      <div className="flex items-center gap-3 py-6 px-4 border-b border-slate-700">
        <Shield className="h-8 w-8 text-blue-400" />
        <span className="text-xl font-bold">FedLearn</span>
      </div>

      <nav className="flex-1 py-4 px-2">
        <ul className="space-y-1">
          {navItems.map((item) => {
            const isActive =
              item.href === "/dashboard"
                ? pathname === "/dashboard"
                : pathname.startsWith(item.href);
            const Icon = item.icon;

            return (
              <li key={item.href}>
                <Link
                  href={item.href}
                  className={cn(
                    "flex items-center gap-3 px-3 py-2.5 rounded-md text-sm font-medium transition-colors",
                    isActive
                      ? "bg-slate-800 text-blue-400"
                      : "text-slate-300 hover:bg-slate-800/50 hover:text-white"
                  )}
                >
                  <Icon className="h-5 w-5" />
                  {item.label}
                </Link>
              </li>
            );
          })}
        </ul>
      </nav>

      <div className="p-4 border-t border-slate-700">
        <button
          onClick={handleLogout}
          className="flex items-center gap-3 px-3 py-2.5 rounded-md text-sm font-medium text-slate-300 hover:bg-slate-800/50 hover:text-white transition-colors w-full"
        >
          <LogOut className="h-5 w-5" />
          Logout
        </button>
      </div>
    </aside>
  );
}

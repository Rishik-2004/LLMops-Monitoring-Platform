"use client";

import { LucideIcon, TrendingUp, TrendingDown } from "lucide-react";
import { cn } from "@/lib/utils";

type Color = "primary" | "accent" | "success" | "warning" | "danger";

interface MetricCardProps {
  title: string;
  value: string;
  sub?: string;
  change?: number;
  icon: LucideIcon;
  color: Color;
  loading?: boolean;
}

const colorMap: Record<Color, { icon: string; glow: string; badge: string }> = {
  primary: {
    icon: "text-indigo-400 bg-indigo-400/10 border-indigo-400/20",
    glow: "hover:glow-primary",
    badge: "text-indigo-400",
  },
  accent: {
    icon: "text-cyan-400 bg-cyan-400/10 border-cyan-400/20",
    glow: "hover:glow-accent",
    badge: "text-cyan-400",
  },
  success: {
    icon: "text-emerald-400 bg-emerald-400/10 border-emerald-400/20",
    glow: "hover:glow-success",
    badge: "text-emerald-400",
  },
  warning: {
    icon: "text-amber-400 bg-amber-400/10 border-amber-400/20",
    glow: "",
    badge: "text-amber-400",
  },
  danger: {
    icon: "text-red-400 bg-red-400/10 border-red-400/20",
    glow: "hover:glow-danger",
    badge: "text-red-400",
  },
};

export function MetricCard({
  title,
  value,
  sub,
  change,
  icon: Icon,
  color,
  loading,
}: MetricCardProps) {
  const c = colorMap[color];

  if (loading) {
    return (
      <div className="metric-card">
        <div className="shimmer h-4 w-24 rounded mb-3" />
        <div className="shimmer h-8 w-16 rounded mb-2" />
        <div className="shimmer h-3 w-20 rounded" />
      </div>
    );
  }

  return (
    <div className={cn("metric-card cursor-default", c.glow)}>
      <div className="flex items-start justify-between mb-3">
        <span className="text-xs text-muted-foreground font-medium">{title}</span>
        <div className={cn("p-1.5 rounded-lg border", c.icon)}>
          <Icon className="w-3.5 h-3.5" />
        </div>
      </div>

      <div className="text-2xl font-bold tracking-tight mb-1">{value}</div>

      <div className="flex items-center justify-between">
        {sub && (
          <span className="text-[11px] text-muted-foreground">{sub}</span>
        )}
        {typeof change === "number" && (
          <div
            className={cn(
              "flex items-center gap-1 text-[11px] font-medium",
              change >= 0 ? "text-emerald-400" : "text-red-400"
            )}
          >
            {change >= 0 ? (
              <TrendingUp className="w-3 h-3" />
            ) : (
              <TrendingDown className="w-3 h-3" />
            )}
            {Math.abs(change).toFixed(1)}%
          </div>
        )}
      </div>
    </div>
  );
}

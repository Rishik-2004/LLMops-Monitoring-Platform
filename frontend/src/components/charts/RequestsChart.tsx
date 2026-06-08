"use client";

import { useQuery } from "@tanstack/react-query";
import { analyticsApi } from "@/lib/api";
import {
  AreaChart,
  Area,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
} from "recharts";
import { format } from "date-fns";
import { Activity } from "lucide-react";

const CustomTooltip = ({ active, payload, label }: any) => {
  if (active && payload?.length) {
    return (
      <div className="bg-card border border-border rounded-lg px-3 py-2 shadow-xl text-xs">
        <p className="text-muted-foreground mb-1">{label}</p>
        <p className="font-semibold text-primary">
          {payload[0]?.value?.toLocaleString()} requests
        </p>
      </div>
    );
  }
  return null;
};

export function RequestsChart() {
  const { data, isLoading } = useQuery({
    queryKey: ["timeseries", "requests"],
    queryFn: () =>
      analyticsApi
        .timeseries({ metric: "requests", granularity: "day", days: 14 })
        .then((r) => r.data),
  });

  const chartData = (data ?? []).map((d: any) => ({
    date: format(new Date(d.timestamp), "MMM d"),
    value: d.value,
  }));

  return (
    <div className="card-glass rounded-xl p-5">
      <div className="flex items-center gap-2 mb-4">
        <div className="p-1.5 rounded-lg bg-indigo-400/10 border border-indigo-400/20">
          <Activity className="w-3.5 h-3.5 text-indigo-400" />
        </div>
        <div>
          <p className="text-sm font-semibold">Request Volume</p>
          <p className="text-xs text-muted-foreground">Last 14 days</p>
        </div>
      </div>

      {isLoading ? (
        <div className="shimmer h-48 rounded-lg" />
      ) : (
        <ResponsiveContainer width="100%" height={200}>
          <AreaChart data={chartData}>
            <defs>
              <linearGradient id="reqGrad" x1="0" y1="0" x2="0" y2="1">
                <stop offset="5%" stopColor="#6366f1" stopOpacity={0.3} />
                <stop offset="95%" stopColor="#6366f1" stopOpacity={0} />
              </linearGradient>
            </defs>
            <CartesianGrid
              strokeDasharray="3 3"
              stroke="hsl(222 47% 14%)"
              vertical={false}
            />
            <XAxis
              dataKey="date"
              tick={{ fontSize: 11, fill: "hsl(215 20% 55%)" }}
              axisLine={false}
              tickLine={false}
            />
            <YAxis
              tick={{ fontSize: 11, fill: "hsl(215 20% 55%)" }}
              axisLine={false}
              tickLine={false}
              width={40}
            />
            <Tooltip content={<CustomTooltip />} />
            <Area
              type="monotone"
              dataKey="value"
              stroke="#6366f1"
              strokeWidth={2}
              fill="url(#reqGrad)"
              dot={false}
              activeDot={{ r: 4, fill: "#6366f1" }}
            />
          </AreaChart>
        </ResponsiveContainer>
      )}
    </div>
  );
}

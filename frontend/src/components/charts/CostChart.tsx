"use client";

import { useQuery } from "@tanstack/react-query";
import { analyticsApi } from "@/lib/api";
import {
  BarChart,
  Bar,
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  ReferenceLine,
} from "recharts";
import { format } from "date-fns";
import { DollarSign, Zap } from "lucide-react";
import { formatCurrency, formatMs } from "@/lib/utils";

const CostTooltip = ({ active, payload, label }: any) => {
  if (active && payload?.length) {
    return (
      <div className="bg-card border border-border rounded-lg px-3 py-2 shadow-xl text-xs">
        <p className="text-muted-foreground mb-1">{label}</p>
        <p className="font-semibold text-amber-400">
          {formatCurrency(payload[0]?.value ?? 0)}
        </p>
      </div>
    );
  }
  return null;
};

export function CostChart() {
  const { data, isLoading } = useQuery({
    queryKey: ["timeseries", "cost"],
    queryFn: () =>
      analyticsApi
        .timeseries({ metric: "cost", granularity: "day", days: 14 })
        .then((r) => r.data),
  });

  const chartData = (data ?? []).map((d: any) => ({
    date: format(new Date(d.timestamp), "MMM d"),
    value: parseFloat(d.value.toFixed(4)),
  }));

  return (
    <div className="card-glass rounded-xl p-5">
      <div className="flex items-center gap-2 mb-4">
        <div className="p-1.5 rounded-lg bg-amber-400/10 border border-amber-400/20">
          <DollarSign className="w-3.5 h-3.5 text-amber-400" />
        </div>
        <div>
          <p className="text-sm font-semibold">Cost Trend</p>
          <p className="text-xs text-muted-foreground">Daily API spend</p>
        </div>
      </div>

      {isLoading ? (
        <div className="shimmer h-48 rounded-lg" />
      ) : (
        <ResponsiveContainer width="100%" height={200}>
          <BarChart data={chartData} barSize={14}>
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
              width={50}
              tickFormatter={(v) => `$${v.toFixed(2)}`}
            />
            <Tooltip content={<CostTooltip />} />
            <Bar dataKey="value" fill="#f59e0b" radius={[3, 3, 0, 0]} />
          </BarChart>
        </ResponsiveContainer>
      )}
    </div>
  );
}

const LatencyTooltip = ({ active, payload, label }: any) => {
  if (active && payload?.length) {
    return (
      <div className="bg-card border border-border rounded-lg px-3 py-2 shadow-xl text-xs">
        <p className="text-muted-foreground mb-1">{label}</p>
        <p className="font-semibold text-cyan-400">
          {formatMs(payload[0]?.value ?? 0)}
        </p>
      </div>
    );
  }
  return null;
};

export function LatencyChart() {
  const { data: latency, isLoading } = useQuery({
    queryKey: ["timeseries", "latency"],
    queryFn: () =>
      analyticsApi
        .timeseries({ metric: "latency", granularity: "day", days: 14 })
        .then((r) => r.data),
  });

  const { data: percentiles } = useQuery({
    queryKey: ["analytics", "latency", "percentiles"],
    queryFn: () => analyticsApi.latencyPercentiles().then((r) => r.data),
  });

  const chartData = (latency ?? []).map((d: any) => ({
    date: format(new Date(d.timestamp), "MMM d"),
    value: parseFloat((d.value ?? 0).toFixed(1)),
  }));

  return (
    <div className="card-glass rounded-xl p-5">
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center gap-2">
          <div className="p-1.5 rounded-lg bg-cyan-400/10 border border-cyan-400/20">
            <Zap className="w-3.5 h-3.5 text-cyan-400" />
          </div>
          <div>
            <p className="text-sm font-semibold">Latency Trend</p>
            <p className="text-xs text-muted-foreground">Avg response time</p>
          </div>
        </div>

        {percentiles && (
          <div className="flex items-center gap-4 text-xs">
            {[
              { label: "P50", value: percentiles.p50 },
              { label: "P95", value: percentiles.p95 },
              { label: "P99", value: percentiles.p99 },
            ].map(({ label, value }) => (
              <div key={label} className="text-center">
                <p className="text-muted-foreground">{label}</p>
                <p className="font-semibold text-cyan-400">
                  {formatMs(value)}
                </p>
              </div>
            ))}
          </div>
        )}
      </div>

      {isLoading ? (
        <div className="shimmer h-52 rounded-lg" />
      ) : (
        <ResponsiveContainer width="100%" height={220}>
          <LineChart data={chartData}>
            <defs>
              <linearGradient id="latGrad" x1="0" y1="0" x2="0" y2="1">
                <stop offset="5%" stopColor="#06b6d4" stopOpacity={0.15} />
                <stop offset="95%" stopColor="#06b6d4" stopOpacity={0} />
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
              width={55}
              tickFormatter={(v) => `${v}ms`}
            />
            <Tooltip content={<LatencyTooltip />} />
            <ReferenceLine
              y={3000}
              stroke="#ef4444"
              strokeDasharray="4 4"
              strokeWidth={1}
              label={{ value: "Alert", fill: "#ef4444", fontSize: 10 }}
            />
            <Line
              type="monotone"
              dataKey="value"
              stroke="#06b6d4"
              strokeWidth={2}
              dot={false}
              activeDot={{ r: 4, fill: "#06b6d4" }}
            />
          </LineChart>
        </ResponsiveContainer>
      )}
    </div>
  );
}

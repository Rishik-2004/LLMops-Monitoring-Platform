"use client";

import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { usersApi } from "@/lib/api";
import { toast } from "sonner";
import { Users, Shield, UserCheck, UserX } from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { timeAgo, cn } from "@/lib/utils";

const roleColors: Record<string, string> = {
  superadmin: "text-red-400 bg-red-400/10 border-red-400/20",
  admin: "text-amber-400 bg-amber-400/10 border-amber-400/20",
  developer: "text-indigo-400 bg-indigo-400/10 border-indigo-400/20",
  viewer: "text-muted-foreground bg-secondary border-border",
};

export default function UsersPage() {
  const qc = useQueryClient();

  const { data, isLoading } = useQuery({
    queryKey: ["users"],
    queryFn: () => usersApi.list().then((r) => r.data),
  });

  const toggleStatus = useMutation({
    mutationFn: (id: string) => usersApi.toggleStatus(id),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["users"] });
      toast.success("User status updated");
    },
  });

  const updateRole = useMutation({
    mutationFn: ({ id, role }: { id: string; role: string }) =>
      usersApi.updateRole(id, role),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["users"] });
      toast.success("Role updated");
    },
  });

  const users = data?.items ?? [];

  return (
    <div className="p-6 space-y-6 animate-fade-in">
      <div className="flex items-center gap-3">
        <Users className="w-5 h-5 text-primary" />
        <div>
          <h1 className="text-xl font-bold">User Management</h1>
          <p className="text-sm text-muted-foreground">
            {users.length} registered users
          </p>
        </div>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-4 gap-4">
        {[
          { label: "Total Users", value: users.length, icon: Users },
          { label: "Active", value: users.filter((u: any) => u.is_active).length, icon: UserCheck },
          { label: "Admins", value: users.filter((u: any) => ["admin","superadmin"].includes(u.role)).length, icon: Shield },
          { label: "Inactive", value: users.filter((u: any) => !u.is_active).length, icon: UserX },
        ].map(({ label, value, icon: Icon }) => (
          <div key={label} className="metric-card">
            <p className="text-xs text-muted-foreground">{label}</p>
            <p className="text-2xl font-bold mt-1">{value}</p>
          </div>
        ))}
      </div>

      {/* Table */}
      <div className="card-glass rounded-xl overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full text-xs">
            <thead className="bg-secondary/50 border-b border-border/50">
              <tr>
                {["User", "Email", "Role", "Status", "Last Login", "Joined", "Actions"].map((h) => (
                  <th key={h} className="text-left px-4 py-3 text-muted-foreground font-medium">
                    {h}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody>
              {isLoading
                ? [...Array(5)].map((_, i) => (
                    <tr key={i} className="border-b border-border/30">
                      {[...Array(7)].map((_, j) => (
                        <td key={j} className="px-4 py-3">
                          <div className="shimmer h-4 rounded w-20" />
                        </td>
                      ))}
                    </tr>
                  ))
                : users.map((u: any) => (
                    <tr
                      key={u.id}
                      className="border-b border-border/30 hover:bg-secondary/30 transition-colors"
                    >
                      <td className="px-4 py-3">
                        <div className="flex items-center gap-2">
                          <div className="w-7 h-7 rounded-lg bg-primary/20 border border-primary/20 flex items-center justify-center text-primary text-xs font-bold">
                            {u.username?.[0]?.toUpperCase()}
                          </div>
                          <span className="font-medium">{u.username}</span>
                        </div>
                      </td>
                      <td className="px-4 py-3 text-muted-foreground">{u.email}</td>
                      <td className="px-4 py-3">
                        <select
                          value={u.role}
                          onChange={(e) =>
                            updateRole.mutate({ id: u.id, role: e.target.value })
                          }
                          className="bg-secondary border border-border rounded px-2 py-1 text-xs"
                        >
                          <option value="viewer">Viewer</option>
                          <option value="developer">Developer</option>
                          <option value="admin">Admin</option>
                          <option value="superadmin">Superadmin</option>
                        </select>
                      </td>
                      <td className="px-4 py-3">
                        <Badge
                          variant="outline"
                          className={cn(
                            "text-[10px]",
                            u.is_active
                              ? "text-emerald-400 bg-emerald-400/10 border-emerald-400/20"
                              : "text-red-400 bg-red-400/10 border-red-400/20"
                          )}
                        >
                          {u.is_active ? "Active" : "Inactive"}
                        </Badge>
                      </td>
                      <td className="px-4 py-3 text-muted-foreground">
                        {u.last_login ? timeAgo(u.last_login) : "Never"}
                      </td>
                      <td className="px-4 py-3 text-muted-foreground">
                        {timeAgo(u.created_at)}
                      </td>
                      <td className="px-4 py-3">
                        <Button
                          variant="ghost"
                          size="sm"
                          className="h-6 text-[10px]"
                          onClick={() => toggleStatus.mutate(u.id)}
                        >
                          {u.is_active ? (
                            <UserX className="w-3 h-3 mr-1 text-red-400" />
                          ) : (
                            <UserCheck className="w-3 h-3 mr-1 text-emerald-400" />
                          )}
                          {u.is_active ? "Deactivate" : "Activate"}
                        </Button>
                      </td>
                    </tr>
                  ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}

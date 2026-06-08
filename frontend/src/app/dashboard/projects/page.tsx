"use client";

import { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { projectsApi } from "@/lib/api";
import { toast } from "sonner";
import { FolderOpen, Plus, Key, Trash2, Edit, Copy, Eye, EyeOff } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Badge } from "@/components/ui/badge";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { timeAgo, cn } from "@/lib/utils";

const envColors: Record<string, string> = {
  production: "text-emerald-400 bg-emerald-400/10 border-emerald-400/20",
  staging: "text-amber-400 bg-amber-400/10 border-amber-400/20",
  development: "text-blue-400 bg-blue-400/10 border-blue-400/20",
};

export default function ProjectsPage() {
  const qc = useQueryClient();
  const [creating, setCreating] = useState(false);
  const [newKey, setNewKey] = useState<string | null>(null);
  const [showKey, setShowKey] = useState(false);
  const [form, setForm] = useState({ name: "", description: "", environment: "development" });
  const [selectedProject, setSelectedProject] = useState<any>(null);

  const { data, isLoading } = useQuery({
    queryKey: ["projects"],
    queryFn: () => projectsApi.list().then((r) => r.data),
  });

  const { data: apiKeys } = useQuery({
    queryKey: ["apikeys", selectedProject?.id],
    queryFn: () => projectsApi.listApiKeys(selectedProject!.id).then((r) => r.data),
    enabled: !!selectedProject,
  });

  const createProject = useMutation({
    mutationFn: () => projectsApi.create(form),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["projects"] });
      toast.success("Project created");
      setCreating(false);
      setForm({ name: "", description: "", environment: "development" });
    },
    onError: () => toast.error("Failed to create project"),
  });

  const deleteProject = useMutation({
    mutationFn: (id: string) => projectsApi.delete(id),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["projects"] });
      toast.success("Project deleted");
    },
  });

  const generateKey = useMutation({
    mutationFn: (projectId: string) =>
      projectsApi.createApiKey(projectId, { name: "Default Key", permissions: "read,write" }),
    onSuccess: (res) => {
      qc.invalidateQueries({ queryKey: ["apikeys", selectedProject?.id] });
      setNewKey(res.data.plain_key);
      toast.success("API key generated — save it now, it won't be shown again!");
    },
  });

  const revokeKey = useMutation({
    mutationFn: ({ projectId, keyId }: { projectId: string; keyId: string }) =>
      projectsApi.revokeApiKey(projectId, keyId),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["apikeys", selectedProject?.id] });
      toast.success("API key revoked");
    },
  });

  const projects = data?.items ?? [];

  return (
    <div className="p-6 space-y-6 animate-fade-in">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <FolderOpen className="w-5 h-5 text-primary" />
          <div>
            <h1 className="text-xl font-bold">Projects</h1>
            <p className="text-sm text-muted-foreground">{projects.length} projects</p>
          </div>
        </div>
        <Button
          size="sm"
          onClick={() => setCreating(true)}
          className="bg-primary hover:bg-primary/90"
        >
          <Plus className="w-4 h-4 mr-1.5" />
          New Project
        </Button>
      </div>

      {/* Projects Grid */}
      {isLoading ? (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {[...Array(3)].map((_, i) => (
            <div key={i} className="shimmer h-40 rounded-xl" />
          ))}
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {projects.map((p: any) => (
            <div
              key={p.id}
              className="card-glass rounded-xl p-5 hover:border-primary/30 transition-all cursor-pointer group"
              onClick={() => setSelectedProject(p)}
            >
              <div className="flex items-start justify-between mb-3">
                <div className="flex items-center justify-center w-9 h-9 rounded-lg bg-primary/10 border border-primary/20">
                  <FolderOpen className="w-4 h-4 text-primary" />
                </div>
                <Badge
                  variant="outline"
                  className={cn("text-[10px]", envColors[p.environment] ?? envColors.development)}
                >
                  {p.environment}
                </Badge>
              </div>
              <h3 className="font-semibold mb-1">{p.name}</h3>
              <p className="text-xs text-muted-foreground line-clamp-2 mb-3">
                {p.description ?? "No description"}
              </p>
              <div className="flex items-center justify-between text-[10px] text-muted-foreground">
                <span>Created {timeAgo(p.created_at)}</span>
                <div className="flex gap-1.5 opacity-0 group-hover:opacity-100 transition-opacity">
                  <button
                    onClick={(e) => { e.stopPropagation(); setSelectedProject(p); }}
                    className="p-1 rounded hover:bg-secondary"
                  >
                    <Key className="w-3.5 h-3.5" />
                  </button>
                  <button
                    onClick={(e) => { e.stopPropagation(); deleteProject.mutate(p.id); }}
                    className="p-1 rounded hover:bg-destructive/10 hover:text-red-400"
                  >
                    <Trash2 className="w-3.5 h-3.5" />
                  </button>
                </div>
              </div>
            </div>
          ))}

          {projects.length === 0 && (
            <div className="col-span-3 text-center py-16 text-muted-foreground">
              <FolderOpen className="w-10 h-10 mx-auto mb-3 opacity-40" />
              <p className="font-medium">No projects yet</p>
              <p className="text-sm mt-1">Create your first project to start monitoring</p>
            </div>
          )}
        </div>
      )}

      {/* Create Project Dialog */}
      <Dialog open={creating} onOpenChange={setCreating}>
        <DialogContent className="bg-card border-border max-w-md">
          <DialogHeader>
            <DialogTitle>Create New Project</DialogTitle>
          </DialogHeader>
          <div className="space-y-4">
            <div>
              <Label>Project Name *</Label>
              <Input
                value={form.name}
                onChange={(e) => setForm((f) => ({ ...f, name: e.target.value }))}
                placeholder="My AI App"
                className="mt-1.5 bg-secondary border-border"
              />
            </div>
            <div>
              <Label>Description</Label>
              <Input
                value={form.description}
                onChange={(e) => setForm((f) => ({ ...f, description: e.target.value }))}
                placeholder="Optional description"
                className="mt-1.5 bg-secondary border-border"
              />
            </div>
            <div>
              <Label>Environment</Label>
              <select
                value={form.environment}
                onChange={(e) => setForm((f) => ({ ...f, environment: e.target.value }))}
                className="w-full mt-1.5 bg-secondary border border-border rounded-lg px-3 py-2 text-sm"
              >
                <option value="development">Development</option>
                <option value="staging">Staging</option>
                <option value="production">Production</option>
              </select>
            </div>
            <Button
              className="w-full bg-primary hover:bg-primary/90"
              disabled={!form.name || createProject.isPending}
              onClick={() => createProject.mutate()}
            >
              Create Project
            </Button>
          </div>
        </DialogContent>
      </Dialog>

      {/* Project API Keys Dialog */}
      <Dialog open={!!selectedProject} onOpenChange={() => { setSelectedProject(null); setNewKey(null); }}>
        <DialogContent className="bg-card border-border max-w-lg">
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2">
              <Key className="w-4 h-4 text-primary" />
              {selectedProject?.name} — API Keys
            </DialogTitle>
          </DialogHeader>

          {newKey && (
            <div className="p-3 rounded-lg bg-emerald-400/10 border border-emerald-400/20 mb-2">
              <p className="text-xs text-emerald-400 font-semibold mb-1.5">
                ✅ New key generated — copy now, won't be shown again!
              </p>
              <div className="flex items-center gap-2">
                <code className="flex-1 text-xs font-mono bg-background/50 px-2 py-1.5 rounded overflow-hidden">
                  {showKey ? newKey : "•".repeat(40)}
                </code>
                <button onClick={() => setShowKey(!showKey)} className="p-1.5 hover:bg-secondary rounded">
                  {showKey ? <EyeOff className="w-3.5 h-3.5" /> : <Eye className="w-3.5 h-3.5" />}
                </button>
                <button
                  onClick={() => { navigator.clipboard.writeText(newKey); toast.success("Copied!"); }}
                  className="p-1.5 hover:bg-secondary rounded"
                >
                  <Copy className="w-3.5 h-3.5" />
                </button>
              </div>
            </div>
          )}

          <div className="space-y-2">
            {(apiKeys ?? []).map((k: any) => (
              <div key={k.id} className="flex items-center gap-3 p-3 rounded-lg bg-secondary/50 border border-border/50">
                <Key className="w-3.5 h-3.5 text-muted-foreground" />
                <div className="flex-1 min-w-0">
                  <p className="text-xs font-medium">{k.name}</p>
                  <p className="text-[10px] font-mono text-muted-foreground">{k.key_prefix}...</p>
                </div>
                <Badge variant="outline" className={cn("text-[10px]", k.is_active ? "text-emerald-400" : "text-red-400")}>
                  {k.is_active ? "Active" : "Revoked"}
                </Badge>
                {k.is_active && (
                  <button
                    onClick={() => revokeKey.mutate({ projectId: selectedProject.id, keyId: k.id })}
                    className="p-1.5 rounded hover:bg-destructive/10 hover:text-red-400 text-muted-foreground"
                  >
                    <Trash2 className="w-3.5 h-3.5" />
                  </button>
                )}
              </div>
            ))}
            {(apiKeys ?? []).length === 0 && (
              <p className="text-sm text-muted-foreground text-center py-4">No API keys yet</p>
            )}
          </div>

          <Button
            className="w-full bg-primary hover:bg-primary/90 mt-2"
            onClick={() => generateKey.mutate(selectedProject.id)}
            disabled={generateKey.isPending}
          >
            <Key className="w-3.5 h-3.5 mr-1.5" />
            Generate New API Key
          </Button>
        </DialogContent>
      </Dialog>
    </div>
  );
}

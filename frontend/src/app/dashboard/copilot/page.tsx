"use client";

import { useState, useRef, useEffect } from "react";
import { useQuery } from "@tanstack/react-query";
import { copilotApi } from "@/lib/api";
import { toast } from "sonner";
import { Bot, Send, Loader2, Cpu, Sparkles, RefreshCw } from "lucide-react";
import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";
import ReactMarkdown from "react-markdown";

interface Message {
  role: "user" | "assistant";
  content: string;
  reasoning?: string[];
  timestamp: Date;
}

export default function CopilotPage() {
  const [messages, setMessages] = useState<Message[]>([
    {
      role: "assistant",
      content:
        "👋 Hello! I'm your **AI Monitoring Copilot**, powered by LangGraph + Groq.\n\nI can analyze your LLM monitoring data, explain anomalies, identify trends, and recommend optimizations.\n\nTry asking me something like:\n- *Why did costs increase yesterday?*\n- *Which model has the highest latency?*\n- *Give me a weekly operational summary*",
      timestamp: new Date(),
    },
  ]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const bottomRef = useRef<HTMLDivElement>(null);

  const { data: suggestions } = useQuery({
    queryKey: ["copilot", "suggestions"],
    queryFn: () => copilotApi.suggestions().then((r) => r.data.suggestions),
  });

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  const sendMessage = async (text?: string) => {
    const q = text ?? input.trim();
    if (!q || loading) return;

    setInput("");
    setMessages((prev) => [
      ...prev,
      { role: "user", content: q, timestamp: new Date() },
    ]);
    setLoading(true);

    try {
      const { data } = await copilotApi.chat({ question: q });
      setMessages((prev) => [
        ...prev,
        {
          role: "assistant",
          content: data.answer,
          reasoning: data.reasoning_steps,
          timestamp: new Date(),
        },
      ]);
    } catch {
      toast.error("Copilot request failed");
      setMessages((prev) => [
        ...prev,
        {
          role: "assistant",
          content: "⚠️ I encountered an error. Please check your API configuration.",
          timestamp: new Date(),
        },
      ]);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="flex flex-col h-full p-4 gap-4 max-w-4xl mx-auto">
      {/* Header */}
      <div className="flex items-center gap-3">
        <div className="p-2 rounded-xl bg-indigo-400/10 border border-indigo-400/20 glow-primary">
          <Bot className="w-5 h-5 text-indigo-400" />
        </div>
        <div>
          <h1 className="text-lg font-bold gradient-text">AI Monitoring Copilot</h1>
          <p className="text-xs text-muted-foreground">
            LangGraph Agent · Groq LLaMA-3.3-70B · RAG-enhanced
          </p>
        </div>
        <Button
          variant="ghost"
          size="sm"
          className="ml-auto"
          onClick={() =>
            setMessages([
              {
                role: "assistant",
                content: "Chat cleared. How can I help you analyze your LLM operations?",
                timestamp: new Date(),
              },
            ])
          }
        >
          <RefreshCw className="w-3.5 h-3.5 mr-1.5" />
          Clear
        </Button>
      </div>

      {/* Messages */}
      <div className="flex-1 overflow-y-auto scrollbar-thin space-y-4 min-h-0">
        {messages.map((msg, i) => (
          <div
            key={i}
            className={cn(
              "flex gap-3 animate-fade-in",
              msg.role === "user" && "flex-row-reverse"
            )}
          >
            {/* Avatar */}
            <div
              className={cn(
                "w-8 h-8 rounded-lg flex items-center justify-center shrink-0 border",
                msg.role === "assistant"
                  ? "bg-indigo-400/10 border-indigo-400/20"
                  : "bg-cyan-400/10 border-cyan-400/20"
              )}
            >
              {msg.role === "assistant" ? (
                <Cpu className="w-4 h-4 text-indigo-400" />
              ) : (
                <span className="text-xs font-bold text-cyan-400">You</span>
              )}
            </div>

            {/* Bubble */}
            <div
              className={cn(
                "max-w-[80%] rounded-xl px-4 py-3 text-sm",
                msg.role === "assistant"
                  ? "bg-card border border-border/50"
                  : "bg-primary/20 border border-primary/30 ml-auto"
              )}
            >
              <ReactMarkdown
                className="prose prose-invert prose-sm max-w-none prose-p:my-1 prose-ul:my-1 prose-li:my-0.5"
              >
                {msg.content}
              </ReactMarkdown>

              {/* Reasoning steps */}
              {msg.reasoning && msg.reasoning.length > 0 && (
                <details className="mt-2">
                  <summary className="text-[10px] text-muted-foreground cursor-pointer hover:text-foreground">
                    🔍 Reasoning steps ({msg.reasoning.length})
                  </summary>
                  <ul className="mt-1.5 space-y-0.5">
                    {msg.reasoning.map((step, j) => (
                      <li key={j} className="text-[10px] text-muted-foreground flex items-start gap-1.5">
                        <span className="text-primary mt-0.5">→</span>
                        {step}
                      </li>
                    ))}
                  </ul>
                </details>
              )}

              <p className="text-[10px] text-muted-foreground mt-2">
                {msg.timestamp.toLocaleTimeString()}
              </p>
            </div>
          </div>
        ))}

        {loading && (
          <div className="flex gap-3 animate-fade-in">
            <div className="w-8 h-8 rounded-lg flex items-center justify-center bg-indigo-400/10 border border-indigo-400/20">
              <Cpu className="w-4 h-4 text-indigo-400" />
            </div>
            <div className="bg-card border border-border/50 rounded-xl px-4 py-3 flex items-center gap-2">
              <Loader2 className="w-4 h-4 text-indigo-400 animate-spin" />
              <span className="text-xs text-muted-foreground">
                Analyzing your monitoring data...
              </span>
            </div>
          </div>
        )}

        <div ref={bottomRef} />
      </div>

      {/* Suggestions */}
      {messages.length <= 1 && (
        <div className="grid grid-cols-2 gap-2">
          {(suggestions ?? []).slice(0, 4).map((s: string, i: number) => (
            <button
              key={i}
              onClick={() => sendMessage(s)}
              className="text-left px-3 py-2.5 rounded-lg bg-secondary hover:bg-secondary/80 border border-border/50 text-xs text-muted-foreground hover:text-foreground transition-colors group"
            >
              <Sparkles className="w-3 h-3 text-primary mb-1 group-hover:text-primary" />
              {s}
            </button>
          ))}
        </div>
      )}

      {/* Input */}
      <div className="flex gap-2 bg-card border border-border/50 rounded-xl p-2">
        <input
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={(e) => e.key === "Enter" && !e.shiftKey && sendMessage()}
          placeholder="Ask about costs, latency, errors, hallucinations..."
          className="flex-1 bg-transparent text-sm outline-none px-2 placeholder:text-muted-foreground"
          disabled={loading}
        />
        <Button
          size="sm"
          disabled={!input.trim() || loading}
          onClick={() => sendMessage()}
          className="bg-primary hover:bg-primary/90 shrink-0"
        >
          {loading ? (
            <Loader2 className="w-4 h-4 animate-spin" />
          ) : (
            <Send className="w-4 h-4" />
          )}
        </Button>
      </div>
    </div>
  );
}

"use client";

import { useEffect, useState } from "react";
import { Header } from "@/components/dashboard/Header";
import { StatusGrid } from "@/components/dashboard/StatusGrid";
import { Terminal } from "@/components/dashboard/Terminal";
import { ChatPanel } from "@/components/dashboard/ChatPanel";
import { ActionHistory } from "@/components/dashboard/ActionHistory";
import { useLogs } from "@/hooks/use-logs";
import { api, StatusResponse } from "@/lib/api";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Activity, Zap } from "lucide-react";

export default function Home() {
  const { logs, isConnected } = useLogs();
  const [services, setServices] = useState<StatusResponse | null>(null);

  useEffect(() => {
    const fetchStatus = async () => {
      try {
        const data = await api.getStatus();
        setServices(data);
      } catch (e) {
        console.error("Failed to fetch status", e);
      }
    };
    fetchStatus();
  }, []);

  useEffect(() => {
    if (logs.length > 0) {
      const lastLog = logs[logs.length - 1];
      if (lastLog.type === "status_update" && lastLog.details) {
        // Use setTimeout to avoid synchronous state update warning
        setTimeout(() => {
          setServices(lastLog.details as StatusResponse);
        }, 0);
      }
    }
  }, [logs]);

  return (
    <main className="min-h-screen bg-background text-foreground p-4 md:p-6 lg:p-8 max-w-[1600px] mx-auto space-y-8 animate-in fade-in duration-500">
      <Header />

      <section className="space-y-4">
        <div className="flex items-center justify-between">
          <h2 className="text-lg font-semibold tracking-tight flex items-center gap-2">
            <Activity className="w-4 h-4 text-primary" />
            Service Status
          </h2>
          <div className="flex items-center gap-2">
            <span className={`w-2 h-2 rounded-full ${isConnected ? 'bg-green-500 animate-pulse' : 'bg-red-500'}`} />
            <span className="text-xs text-muted-foreground bg-muted px-2 py-1 rounded-full font-mono">
              {isConnected ? 'Real-time via WebSocket' : 'Connecting...'}
            </span>
          </div>
        </div>
        <StatusGrid services={services} />
      </section>

      <div className="grid grid-cols-1 xl:grid-cols-3 gap-6 lg:gap-8 h-full">
        <div className="xl:col-span-2 space-y-6 flex flex-col">
          <Tabs defaultValue="terminal" className="w-full flex-1 flex flex-col">
            <div className="flex items-center justify-between mb-4">
              <TabsList className="bg-muted/50 border border-border/50">
                <TabsTrigger value="terminal" className="data-[state=active]:bg-background">
                  Result Terminal
                </TabsTrigger>
                <TabsTrigger value="history" className="data-[state=active]:bg-background">
                  Action History
                </TabsTrigger>
              </TabsList>
            </div>

            <TabsContent value="terminal" className="mt-0 flex-1">
              <Terminal logs={logs} />
            </TabsContent>

            <TabsContent value="history" className="mt-0 flex-1">
              <ActionHistory logs={logs} />
            </TabsContent>
          </Tabs>
        </div>

        <div className="space-y-6 flex flex-col">
          <ChatPanel />

          <div className="p-5 rounded-xl border bg-gradient-to-br from-card to-muted/20 text-xs text-muted-foreground shadow-sm">
            <h3 className="font-semibold text-foreground mb-3 flex items-center gap-2">
              <Zap className="w-3 h-3 text-yellow-500" />
              System Metrics
            </h3>
            <div className="space-y-2">
              <div className="flex justify-between py-1 border-b border-dashed border-border/50">
                <span>Agent Mode</span>
                <span className="font-mono bg-blue-500/10 text-blue-500 px-1.5 rounded text-[10px]">ON-DEMAND</span>
              </div>
              <div className="flex justify-between py-1 border-b border-dashed border-border/50">
                <span>Monitored Services</span>
                <span className="font-mono text-foreground">{services ? Object.keys(services).length : '-'}</span>
              </div>
              <div className="flex justify-between py-1 border-b border-dashed border-border/50">
                <span>WebSocket Stream</span>
                <span className={`font-mono ${isConnected ? 'text-green-400' : 'text-red-400'}`}>
                  {isConnected ? 'Connected' : 'Disconnected'}
                </span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </main>
  );
}

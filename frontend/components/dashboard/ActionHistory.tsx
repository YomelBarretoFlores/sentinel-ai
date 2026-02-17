import React from 'react';
import { LogEntry } from "@/hooks/use-logs";
import { CheckCircle2, XCircle, AlertTriangle, Play, Shield, Terminal } from "lucide-react";
import { ScrollArea } from "@/components/ui/scroll-area";

interface ActionHistoryProps {
    logs: LogEntry[];
}

export function ActionHistory({ logs }: ActionHistoryProps) {
    // Filter for high-level actions only
    const actions = logs.filter(log =>
        ['plan', 'execute', 'verify', 'approve', 'escalation', 'error'].includes(log.type.toLowerCase())
    ).reverse(); // Newest first

    const getIcon = (type: string) => {
        switch (type.toLowerCase()) {
            case 'plan': return <Terminal className="w-4 h-4 text-purple-400" />;
            case 'execute': return <Play className="w-4 h-4 text-orange-400" />;
            case 'verify': return <CheckCircle2 className="w-4 h-4 text-blue-400" />;
            case 'approve': return <Shield className="w-4 h-4 text-yellow-400" />;
            case 'error': return <XCircle className="w-4 h-4 text-red-500" />;
            case 'escalation': return <AlertTriangle className="w-4 h-4 text-red-500" />;
            default: return <div className="w-4 h-4 rounded-full bg-gray-500" />;
        }
    };

    if (actions.length === 0) {
        return (
            <div className="h-[500px] border rounded-lg flex flex-col items-center justify-center bg-muted/10 text-muted-foreground border-dashed gap-4">
                <Terminal className="w-10 h-10 opacity-20" />
                <p>No high-level actions recorded yet.</p>
            </div>
        );
    }

    return (
        <ScrollArea className="h-[500px] rounded-lg border bg-card/50 backdrop-blur-sm p-4">
            <div className="space-y-4 pr-4">
                {actions.map((action, i) => (
                    <div key={i} className="flex gap-4 p-3 rounded-lg border bg-background/50 hover:bg-background/80 transition-colors">
                        <div className="mt-1">
                            {getIcon(action.type)}
                        </div>
                        <div className="flex-1 space-y-1">
                            <div className="flex items-center justify-between">
                                <span className="text-xs font-bold uppercase tracking-wider opacity-70 border px-1.5 py-0.5 rounded text-foreground/80">
                                    {action.type}
                                </span>
                                <span className="text-[10px] text-muted-foreground font-mono">
                                    {new Date(action.timestamp).toLocaleTimeString()}
                                </span>
                            </div>
                            <p className="text-sm font-mono text-muted-foreground break-all">
                                {action.message}
                            </p>
                        </div>
                    </div>
                ))}
            </div>
        </ScrollArea>
    );
}

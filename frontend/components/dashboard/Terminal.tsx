import React, { useEffect, useRef } from 'react';
import { Terminal as TerminalIcon } from "lucide-react";
import { LogEntry } from "@/hooks/use-logs";

interface TerminalProps {
    logs: LogEntry[];
}

export function Terminal({ logs }: TerminalProps) {
    const endRef = useRef<HTMLDivElement>(null);

    useEffect(() => {
        endRef.current?.scrollIntoView({ behavior: "smooth" });
    }, [logs]);

    const getLogColor = (type: string) => {
        switch (type.toLowerCase()) {
            case 'error': return 'text-red-400';
            case 'warning': return 'text-yellow-400';
            case 'success': return 'text-green-400';
            case 'monitor': return 'text-blue-300';
            case 'plan': return 'text-purple-400';
            case 'execute': return 'text-orange-400';
            case 'system': return 'text-gray-400 italic';
            default: return 'text-gray-300';
        }
    };

    return (
        <div className="rounded-lg border bg-black/40 backdrop-blur-xl shadow-inner h-[500px] flex flex-col font-mono text-sm overflow-hidden">
            <div className="flex items-center px-4 py-2 border-b bg-muted/20">
                <TerminalIcon className="w-4 h-4 mr-2 opacity-50" />
                <span className="text-xs font-semibold opacity-70">Live Agent Logs</span>
                <div className="ml-auto flex space-x-1">
                    <div className="w-2 h-2 rounded-full bg-red-500/50" />
                    <div className="w-2 h-2 rounded-full bg-yellow-500/50" />
                    <div className="w-2 h-2 rounded-full bg-green-500/50" />
                </div>
            </div>

            <div className="flex-1 overflow-y-auto p-4 space-y-1 font-mono text-sm scrollbar-thin scrollbar-thumb-gray-700 scrollbar-track-transparent">
                {logs.map((log, i) => (
                    <div key={i} className="flex gap-2 animate-in fade-in duration-300">
                        <span className="text-muted-foreground whitespace-nowrap text-xs opacity-50 select-none">
                            [{new Date(log.timestamp).toLocaleTimeString()}]
                        </span>
                        <span className={`flex-1 break-all ${getLogColor(log.type)}`}>
                            <span className="font-bold opacity-80 mr-2 uppercase text-[10px] tracking-wider border border-current px-1 rounded-sm">
                                {log.type}
                            </span>
                            {log.message}
                        </span>
                    </div>
                ))}
                <div ref={endRef} />
            </div>
        </div>
    );
}

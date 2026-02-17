import { useState, useEffect } from 'react';
import { Bot, Play, Square } from "lucide-react";
import { Button } from "@/components/ui/button";
import { api, AgentState } from "@/lib/api";
import {
    Dialog,
    DialogContent,
    DialogDescription,
    DialogFooter,
    DialogHeader,
    DialogTitle,
    DialogTrigger,
} from "@/components/ui/dialog";

export function Header() {
    const [agentState, setAgentState] = useState<AgentState>({
        status: 'idle',
        last_run: null,
        current_step: null
    });
    const [isDialogOpen, setIsDialogOpen] = useState(false);

    const refreshState = async () => {
        try {
            const state = await api.getAgentState();
            setAgentState(state);
        } catch (e) {
            console.error("Failed to check agent state", e);
        }
    };

    useEffect(() => {
        let mounted = true;
        const poll = async () => {
            try {
                const state = await api.getAgentState();
                if (mounted) setAgentState(state);
            } catch (e) {
                console.error("Polling error", e);
            }
        };

        poll();
        const interval = setInterval(poll, 2000);
        return () => {
            mounted = false;
            clearInterval(interval);
        };
    }, []); // Empty dependency array, stable

    const handleRunScan = async () => {
        if (agentState.status === 'running') return;
        try {
            setAgentState((prev) => ({ ...prev, status: 'running' }));
            await api.runAgent();
            console.log("Agente iniciado");
        } catch (e) {
            console.error("Failed to start agent", e);
            setAgentState((prev) => ({ ...prev, status: 'idle' }));
        }
    };

    const handleStop = async () => {
        try {
            await api.stopAgent();
            console.log("Señal de parada enviada");
            refreshState();
        } catch (error) {
            console.error(error);
        }
    };

    const handleApprove = async (action: 'approve' | 'reject') => {
        try {
            await api.approveAgent(action);
            console.log(`Acción enviada: ${action}`);
            setIsDialogOpen(false);
            refreshState();
        } catch (error) {
            console.error(error);
        }
    };

    const renderActions = () => {
        if (agentState.status === 'waiting') {
            return (
                <div className="flex gap-2">
                    <Dialog open={isDialogOpen} onOpenChange={setIsDialogOpen}>
                        <DialogTrigger asChild>
                            <Button
                                className="bg-yellow-500/20 hover:bg-yellow-500/40 text-yellow-500 border border-yellow-500/50 animate-pulse"
                            >
                                Review Actions
                            </Button>
                        </DialogTrigger>
                        <DialogContent className="sm:max-w-md">
                            <DialogHeader>
                                <DialogTitle>Approval Required</DialogTitle>
                                <DialogDescription>
                                    The agent has proposed the following critical commands:
                                </DialogDescription>
                            </DialogHeader>
                            <div className="p-4 bg-muted/50 rounded-md font-mono text-xs overflow-x-auto whitespace-pre-wrap border max-h-[200px] overflow-y-auto">
                                {agentState.candidate_plan || "No commands found."}
                            </div>
                            <DialogFooter className="sm:justify-between">
                                <Button
                                    variant="ghost"
                                    onClick={() => handleApprove('reject')}
                                    className="text-red-400 hover:text-red-300 hover:bg-red-400/10"
                                >
                                    Reject Execution
                                </Button>
                                <div className="flex gap-2">
                                    <Button
                                        variant="outline"
                                        onClick={() => setIsDialogOpen(false)}
                                    >
                                        Cancel
                                    </Button>
                                    <Button
                                        onClick={() => handleApprove('approve')}
                                        className="bg-green-600 hover:bg-green-700 text-white"
                                    >
                                        Approve & Run
                                    </Button>
                                </div>
                            </DialogFooter>
                        </DialogContent>
                    </Dialog>

                    <Button
                        variant="outline"
                        onClick={handleStop}
                        className="border-red-900/50 text-red-400 hover:bg-red-900/20"
                    >
                        <Square className="w-4 h-4" />
                    </Button>
                </div>
            );
        }

        if (agentState.status === 'running') {
            return (
                <Button
                    variant="destructive"
                    onClick={handleStop}
                    className="bg-red-900/20 hover:bg-red-900/40 text-red-400 border border-red-900/50"
                >
                    <Square className="w-4 h-4 mr-2 fill-current" />
                    Stop Agent
                </Button>
            );
        }

        return (
            <Button
                onClick={handleRunScan}
                disabled={agentState.status !== 'idle' && agentState.status !== 'error' && agentState.status !== 'completed'}
                className="bg-primary hover:bg-primary/90 gap-2"
            >
                <Play className="w-4 h-4 fill-current" />
                Run Agent Scan
            </Button>
        );
    };

    return (
        <div className="flex items-center justify-between py-6">
            <div className="flex items-center gap-3">
                <div className="bg-primary/10 p-2 rounded-lg border border-primary/20">
                    <Bot className="h-6 w-6 text-primary" />
                </div>
                <div>
                    <h1 className="text-2xl font-bold tracking-tight bg-gradient-to-r from-white to-gray-400 bg-clip-text text-transparent">
                        Sentinel AI
                    </h1>
                    <p className="text-sm text-muted-foreground">
                        Autonomous DevOps Remediation Agent
                    </p>
                </div>
            </div>
            <div className="flex items-center gap-4">
                <div className="flex flex-col items-end">
                    <div className="flex items-center gap-2">
                        {agentState.status === 'running' && (
                            <span className="flex h-2 w-2 rounded-full bg-green-500 animate-pulse" />
                        )}
                        {agentState.status === 'waiting' && (
                            <span className="flex h-2 w-2 rounded-full bg-yellow-500 animate-ping" />
                        )}
                        <span className="text-sm font-medium uppercase tracking-wider opacity-70">
                            {agentState.status === 'waiting' ? 'WAITING APPROVAL' : agentState.status}
                        </span>
                    </div>
                    {agentState.last_run && (
                        <span className="text-xs text-muted-foreground">
                            Last run: {new Date(agentState.last_run).toLocaleTimeString()}
                        </span>
                    )}
                </div>

                <div className="h-8 w-px bg-border hidden sm:block" />

                {renderActions()}
            </div>
        </div>
    );
}

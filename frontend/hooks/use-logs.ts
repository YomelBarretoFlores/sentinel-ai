import { useState, useEffect, useRef } from 'react';
import { StatusResponse } from "@/lib/api";

export interface LogEntry {
    timestamp: string;
    type: string;
    message: string;
    details?: StatusResponse | Record<string, unknown>;
}

export function useLogs() {
    const [logs, setLogs] = useState<LogEntry[]>([]);
    const [isConnected, setIsConnected] = useState(false);
    const ws = useRef<WebSocket | null>(null);

    useEffect(() => {
        let reconnectTimeout: NodeJS.Timeout;
        let mounted = true;

        const connect = () => {
            const socket = new WebSocket('ws://localhost:8000/ws/logs');

            socket.onopen = () => {
                if (mounted) setIsConnected(true);
                setLogs(prev => [...prev, {
                    timestamp: new Date().toISOString(),
                    type: 'system',
                    message: 'Connected to Sentinel AI Event Stream'
                }]);
            };

            socket.onmessage = (event) => {
                try {
                    const data = JSON.parse(event.data);
                    if (mounted) {
                        setLogs(prev => {
                            const newLogs = [...prev, data];
                            return newLogs.slice(-500);
                        });
                    }
                } catch (e) {
                    console.error("Error parsing socket message", e);
                }
            };

            socket.onclose = () => {
                if (mounted) setIsConnected(false);
                reconnectTimeout = setTimeout(connect, 5000);
            };

            socket.onerror = (err) => {
                console.error("WebSocket error", err);
                socket.close();
            };

            ws.current = socket;
        };

        connect();

        return () => {
            mounted = false;
            if (ws.current) ws.current.close();
            clearTimeout(reconnectTimeout);
        };
    }, []);

    const clearLogs = () => setLogs([]);

    return { logs, isConnected, clearLogs };
}

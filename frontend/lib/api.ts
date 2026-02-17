import axios from 'axios';

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

export interface ServiceStatus {
    status: 'running' | 'stopped' | 'error';
    details: string;
    type: string;
}

export type StatusResponse = Record<string, ServiceStatus>;

export interface Episode {
    timestamp: string;
    error: string;
    diagnosis: string;
    command: string;
    result: string;
    success: boolean;
}

export interface AgentState {
    status: 'idle' | 'running' | 'completed' | 'error' | 'waiting';
    last_run: string | null;
    current_step: string | null;
    candidate_plan?: string;
}

export interface ChatEvent {
    event: string;
    data: unknown;
}

export const api = {
    getStatus: async () => {
        const response = await axios.get<StatusResponse>(`${API_URL}/status`);
        return response.data;
    },

    getMemory: async () => {
        const response = await axios.get<Episode[]>(`${API_URL}/memory`);
        return response.data;
    },

    getConfig: async () => {
        const response = await axios.get(`${API_URL}/config`);
        return response.data;
    },

    chat: async (query: string) => {
        const response = await axios.post(`${API_URL}/chat`, { query });
        return response.data;
    },

    chatStream: async (query: string, onEvent: (event: ChatEvent) => void) => {
        const response = await fetch(`${API_URL}/chat`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ query })
        });

        if (!response.body) return;

        const reader = response.body.getReader();
        const decoder = new TextDecoder();
        let buffer = '';

        while (true) {
            const { done, value } = await reader.read();
            if (done) break;

            buffer += decoder.decode(value, { stream: true });
            const p = buffer.split('\n\n');
            buffer = p.pop() || ''; // Keep the last partial chunk

            for (const block of p) {
                if (!block.trim()) continue;
                const lines = block.split('\n');
                let eventType = '';
                let data = '';

                for (const line of lines) {
                    if (line.startsWith('event: ')) eventType = line.substring(7);
                    if (line.startsWith('data: ')) data = line.substring(6);
                }

                if (eventType && data) {
                    try {
                        onEvent({ event: eventType, data: JSON.parse(data) });
                    } catch (e) {
                        console.error("Error parsing SSE data", e);
                    }
                }
            }
        }
    },

    // Agent Control
    runAgent: async () => {
        const res = await fetch(`${API_URL}/agent/run`, {
            method: 'POST'
        });
        return res.json();
    },

    stopAgent: async (): Promise<{ status: string; message: string }> => {
        const res = await fetch(`${API_URL}/agent/stop`, {
            method: 'POST'
        });
        return res.json();
    },

    approveAgent: async (action: 'approve' | 'reject'): Promise<{ status: string; message: string }> => {
        const response = await fetch(`${API_URL}/agent/approve?action=${action}`, {
            method: 'POST',
        });
        return response.json();
    },

    getAgentState: async (): Promise<AgentState> => {
        const res = await fetch(`${API_URL}/agent/state`);
        return res.json();
    }
};

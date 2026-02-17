import { StatusResponse } from "@/lib/api";
import { CheckCircle2, XCircle, Clock, Globe } from "lucide-react";

interface StatusGridProps {
    services: StatusResponse | null;
}

export function StatusGrid({ services }: StatusGridProps) {
    const getStatusColor = (status: string) => {
        switch (status) {
            case 'running': return 'bg-green-500/10 text-green-500 border-green-500/20';
            case 'stopped': return 'bg-red-500/10 text-red-500 border-red-500/20';
            case 'error': return 'bg-red-500/10 text-red-500 border-red-500/20';
            default: return 'bg-gray-500/10 text-gray-400 border-gray-500/20';
        }
    };

    const getStatusIcon = (status: string) => {
        switch (status) {
            case 'running': return <CheckCircle2 className="w-4 h-4" />;
            case 'stopped': return <XCircle className="w-4 h-4" />;
            case 'error': return <XCircle className="w-4 h-4" />;
            default: return <Clock className="w-4 h-4" />;
        }
    };

    if (!services) return (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 animate-pulse">
            {[1, 2, 3, 4].map((i) => (
                <div key={i} className="h-32 rounded-xl bg-muted/50 border border-border/50" />
            ))}
        </div>
    );

    return (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
            {Object.entries(services).map(([name, service]) => (
                <div
                    key={name}
                    className="p-5 rounded-xl border bg-card text-card-foreground shadow-sm hover:shadow-md transition-all duration-300"
                >
                    <div className="flex items-center justify-between mb-4">
                        <h3 className="font-semibold text-sm capitalize">{name}</h3>
                        <div className={`p-1.5 rounded-full ${service.status === 'running' ? 'bg-blue-500/10' : 'bg-red-500/10'}`}>
                            {service.type === 'database' ? (
                                <span className="text-lg">db</span>
                            ) : (
                                service.type === 'web_server' ? (
                                    <Globe className="w-4 h-4 text-blue-500" />
                                ) : (
                                    <span className="text-lg">sys</span>
                                )
                            )}
                        </div>
                    </div>

                    <div className={`inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-xs font-medium border w-fit mb-3 ${getStatusColor(service.status)}`}>
                        {getStatusIcon(service.status)}
                        {service.status}
                    </div>

                    <p className="text-xs text-muted-foreground truncate font-mono">
                        {service.details}
                    </p>
                </div>
            ))}
        </div>
    );
}

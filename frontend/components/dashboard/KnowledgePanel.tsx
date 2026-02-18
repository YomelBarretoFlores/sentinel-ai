import React from 'react';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Book, FileText, Database, Server, Container, ExternalLink, Shield } from "lucide-react";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";

interface KnowledgeSource {
    id: string;
    title: string;
    description: string;
    type: 'manual' | 'guide' | 'api' | 'internal';
    icon: React.ReactNode;
    tags: string[];
    date: string;
    url?: string;
}

const SOURCES: KnowledgeSource[] = [
    {
        id: 'postgres',
        title: 'PostgreSQL User Manual (PDF)',
        description: 'Manual oficial completo de PostgreSQL. Cubre administración, configuración, SQL avanzado y replicación.',
        type: 'manual',
        icon: <Database className="w-5 h-5 text-blue-400" />,
        tags: ['Database', 'SQL', 'Admin'],
        date: '2025-10-15',
        url: 'https://instaladores.willymen.com/Manuales/Postgres-User.pdf'
    },
    {
        id: 'docker',
        title: 'Docker Practice Guide (PDF)',
        description: 'Referencia técnica para despliegue de contenedores. Comandos CLI, docker-compose.yml y networking.',
        type: 'manual',
        icon: <Container className="w-5 h-5 text-blue-500" />,
        tags: ['DevOps', 'Containers', 'CI/CD'],
        date: '2025-09-20',
        url: 'https://josejuansanchez.org/iaw/practica-docker/index.pdf'
    },
    {
        id: 'nginx',
        title: 'Nginx Official Management Guide (PDF)',
        description: 'Guía de administración de servidores Nginx. Incluye configuración de proxy inverso, balanceo de carga y seguridad.',
        type: 'guide',
        icon: <Server className="w-5 h-5 text-green-400" />,
        tags: ['Web Server', 'Proxy', 'Config'],
        date: '2025-11-02',
        url: 'https://cdn.studio.f5.com/files/k6fem79d/production/35ce3e42d2eb2930619f715b6586ac9a18d5a1e5.pdf'
    },
    {
        id: 'internal_protocols',
        title: 'Sentinel AI Internal Protocols',
        description: 'Guía interna de solución de problemas DevOps y protocolos de seguridad generados por el sistema.',
        type: 'internal',
        icon: <Shield className="w-5 h-5 text-purple-400" />,
        tags: ['System', 'Troubleshooting', 'Security'],
        date: 'Generated',
        url: '#'
    }
];

export function KnowledgePanel() {
    return (
        <Card className="h-full bg-card/50 backdrop-blur-sm border-input shadow-lg flex flex-col animate-in fade-in zoom-in-95 duration-500">
            <CardHeader className="py-4 border-b bg-muted/20">
                <div className="flex items-center justify-between">
                    <div>
                        <CardTitle className="text-lg font-medium flex items-center gap-2">
                            <Book className="w-5 h-5 text-primary" />
                            Biblioteca de Conocimiento RAG
                        </CardTitle>
                        <CardDescription className="text-xs text-muted-foreground mt-1">
                            Fuentes oficiales indexadas en Pinecone y procesadas por Cohere Rerank.
                        </CardDescription>
                    </div>
                    <Badge variant="outline" className="bg-primary/10 text-primary border-primary/20">
                        {SOURCES.length} Fuentes Activas
                    </Badge>
                </div>
            </CardHeader>

            <CardContent className="p-0 flex-1 overflow-hidden">
                <ScrollArea className="h-full">
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4 p-4">
                        {SOURCES.map((source) => (
                            <div
                                key={source.id}
                                className="group relative overflow-hidden rounded-xl border border-border/50 bg-linear-to-br from-card to-muted/20 hover:to-muted/40 transition-all duration-300 hover:shadow-md hover:border-primary/20"
                            >
                                <div className="p-5 space-y-3">
                                    <div className="flex items-start justify-between">
                                        <div className="p-2 rounded-lg bg-background border border-border/50 shadow-sm group-hover:scale-110 transition-transform duration-300">
                                            {source.icon}
                                        </div>
                                        <div className="flex gap-1 flex-wrap justify-end">
                                            {source.tags.map(tag => (
                                                <span key={tag} className="text-[10px] px-1.5 py-0.5 rounded-md bg-muted border border-border/50 text-muted-foreground">
                                                    {tag}
                                                </span>
                                            ))}
                                            {source.type === 'internal' && (
                                                <span className="text-[10px] px-1.5 py-0.5 rounded-md bg-purple-500/10 text-purple-400 border border-purple-500/20">
                                                    Internal
                                                </span>
                                            )}
                                        </div>
                                    </div>

                                    <div>
                                        <h4 className="font-semibold text-foreground group-hover:text-primary transition-colors truncate">
                                            {source.title}
                                        </h4>
                                        <p className="text-xs text-muted-foreground line-clamp-2 mt-1">
                                            {source.description}
                                        </p>
                                    </div>

                                    <div className="pt-3 flex items-center justify-between border-t border-dashed border-border/50">
                                        <span className="text-[10px] text-muted-foreground">
                                            Origen: <span className="font-mono">{source.type === 'manual' || source.type === 'guide' ? 'PDF Externo' : 'Sistema'}</span>
                                        </span>
                                        {source.url && source.url !== '#' ? (
                                            <a href={source.url} target="_blank" rel="noopener noreferrer">
                                                <Button variant="ghost" size="sm" className="h-6 w-6 p-0 rounded-full opacity-0 group-hover:opacity-100 transition-opacity">
                                                    <ExternalLink className="w-3 h-3" />
                                                </Button>
                                            </a>
                                        ) : (
                                            <Button variant="ghost" size="sm" disabled className="h-6 w-6 p-0 rounded-full opacity-0 group-hover:opacity-100 transition-opacity">
                                                <Shield className="w-3 h-3 text-muted-foreground" />
                                            </Button>
                                        )}
                                    </div>
                                </div>
                            </div>
                        ))}
                    </div>
                </ScrollArea>
            </CardContent>
        </Card>
    );
}

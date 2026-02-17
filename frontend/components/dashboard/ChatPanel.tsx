import React, { useState, useRef, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Send, Bot, User, Loader2, ChevronDown, ChevronRight, Brain } from "lucide-react";
import { api } from "@/lib/api";
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import { Collapsible, CollapsibleContent, CollapsibleTrigger } from "@/components/ui/collapsible";

type Role = 'user' | 'assistant';

interface Message {
    role: Role;
    content: string;
    thinking?: string[]; // Log of thinking steps
}

export function ChatPanel() {
    const [input, setInput] = useState('');
    const [loading, setLoading] = useState(false);
    const [messages, setMessages] = useState<Message[]>([
        { role: 'assistant', content: 'Hola, soy Sentinel AI. ¿En qué puedo ayudarte hoy?' }
    ]);
    const scrollEndRef = useRef<HTMLDivElement>(null);

    const scrollToBottom = () => {
        scrollEndRef.current?.scrollIntoView({ behavior: "smooth" });
    };

    useEffect(() => {
        scrollToBottom();
    }, [messages]);

    const handleSend = async (e?: React.FormEvent) => {
        if (e) e.preventDefault();
        if (!input.trim() || loading) return;

        const userMsg = input;
        setInput('');

        // Add user message and a placeholder for assistant
        setMessages(prev => [
            ...prev,
            { role: 'user', content: userMsg },
            { role: 'assistant', content: '', thinking: [] }
        ]);
        setLoading(true);

        try {
            await api.chatStream(userMsg, (event) => {
                setMessages(prev => {
                    const newMessages = [...prev];
                    // Create a shallow copy of the last message to avoid mutating state directly
                    const lastMsgIndex = newMessages.length - 1;
                    const lastMsg = { ...newMessages[lastMsgIndex] };

                    if (event.event === 'thinking') {
                        const step = event.data as string;
                        const currentThinking = lastMsg.thinking ? [...lastMsg.thinking] : [];
                        if (!currentThinking.includes(step)) {
                            lastMsg.thinking = [...currentThinking, step];
                        }
                    } else if (event.event === 'message') {
                        lastMsg.content = (lastMsg.content || "") + (event.data as string);
                    } else if (event.event === 'done') {
                        // done
                    } else if (event.event === 'error') {
                        const errData = event.data as { error: string };
                        lastMsg.content = (lastMsg.content || "") + `\n\n**Error:** ${errData.error}`;
                    }

                    newMessages[lastMsgIndex] = lastMsg;
                    return newMessages;
                });
            });
        } catch (error) {
            console.error("Chat error:", error);
            setMessages(prev => {
                const newMessages = [...prev];
                const lastMsg = { ...newMessages[newMessages.length - 1] };
                lastMsg.content = "Error al conectar con el agente.";
                newMessages[newMessages.length - 1] = lastMsg;
                return newMessages;
            });
        } finally {
            setLoading(false);
        }
    };

    return (
        <Card className="flex flex-col h-[600px] bg-card/50 backdrop-blur-sm border-input shadow-lg animate-in fade-in zoom-in-95 duration-500">
            <CardHeader className="py-3 border-b bg-muted/20">
                <CardTitle className="text-sm font-medium flex items-center gap-2">
                    <Bot className="w-4 h-4 text-primary" />
                    RAG Knowledge Base
                </CardTitle>
            </CardHeader>

            <CardContent className="flex-1 flex flex-col p-0 overflow-hidden relative">
                <ScrollArea className="flex-1 p-4 h-full">
                    <div className="space-y-6 pb-4">
                        {messages.map((m, i) => (
                            <div key={i} className={`flex gap-3 ${m.role === 'user' ? 'justify-end' : 'justify-start'}`}>
                                {m.role === 'assistant' && (
                                    <div className="w-8 h-8 rounded-full bg-primary/10 flex items-center justify-center shrink-0 border border-primary/20 mt-1">
                                        <Bot className="w-4 h-4 text-primary" />
                                    </div>
                                )}

                                <div className={`flex flex-col max-w-[85%] ${m.role === 'user' ? 'items-end' : 'items-start'}`}>
                                    {m.thinking && m.thinking.length > 0 && (
                                        <ThinkingProcess steps={m.thinking} finished={!loading || i < messages.length - 1} />
                                    )}

                                    <div className={`rounded-lg px-4 py-3 text-sm shadow-sm overflow-hidden ${m.role === 'user'
                                        ? 'bg-primary text-primary-foreground'
                                        : 'bg-muted border border-border text-foreground'
                                        }`}>
                                        {/* Render Content */}
                                        {m.role === 'assistant' && !m.content && loading && i === messages.length - 1 ? (
                                            <span className="animate-pulse">Generate response...</span>
                                        ) : (
                                            <div className="prose prose-sm dark:prose-invert max-w-none break-words">
                                                <ReactMarkdown
                                                    remarkPlugins={[remarkGfm]}
                                                    components={{
                                                        p: ({ ...props }) => <div className="mb-2 last:mb-0" {...props} />,
                                                        table: ({ ...props }) => (
                                                            <div className="overflow-auto my-2 rounded border">
                                                                <table className="w-full text-left text-xs" {...props} />
                                                            </div>
                                                        ),
                                                        th: ({ ...props }) => <th className="bg-muted px-2 py-1 font-semibold" {...props} />,
                                                        td: ({ ...props }) => <td className="px-2 py-1 border-t border-border" {...props} />,
                                                        // eslint-disable-next-line @typescript-eslint/no-explicit-any
                                                        code: ({ inline, children, ...props }: any) => {
                                                            return inline ? (
                                                                <code className="bg-muted px-1 rounded font-mono text-xs" {...props}>{children}</code>
                                                            ) : (
                                                                <div className="relative group my-2">
                                                                    <div className="absolute right-2 top-2 opacity-0 group-hover:opacity-100 transition-opacity">
                                                                        <span className="text-[10px] text-muted-foreground bg-background border px-1 rounded">Code</span>
                                                                    </div>
                                                                    <code className="block bg-black/50 p-3 rounded-lg font-mono text-xs overflow-x-auto border border-border/50" {...props}>
                                                                        {children}
                                                                    </code>
                                                                </div>
                                                            )
                                                        }
                                                    }}
                                                >
                                                    {m.content}
                                                </ReactMarkdown>
                                            </div>
                                        )}
                                    </div>
                                </div>

                                {m.role === 'user' && (
                                    <div className="w-8 h-8 rounded-full bg-muted flex items-center justify-center shrink-0 border border-border mt-1">
                                        <User className="w-4 h-4 text-muted-foreground" />
                                    </div>
                                )}
                            </div>
                        ))}
                        <div ref={scrollEndRef} />
                    </div>
                </ScrollArea>

                <div className="p-3 border-t bg-background/50 backdrop-blur-md">
                    <form onSubmit={handleSend} className="flex gap-2">
                        <Input
                            value={input}
                            onChange={(e) => setInput(e.target.value)}
                            placeholder="Ask about infrastructure, commands, or logs..."
                            className="bg-background border-input focus-visible:ring-primary shadow-sm"
                            disabled={loading}
                        />
                        <Button type="submit" size="icon" disabled={loading || !input.trim()}>
                            {loading ? <Loader2 className="w-4 h-4 animate-spin" /> : <Send className="w-4 h-4" />}
                        </Button>
                    </form>
                </div>
            </CardContent>
        </Card>
    );
}

function ThinkingProcess({ steps, finished }: { steps: string[], finished: boolean }) {
    const [isOpen, setIsOpen] = useState(!finished);

    useEffect(() => {
        // Use setTimeout to avoid synchronous state update warning
        const timer = setTimeout(() => {
            if (!finished) setIsOpen(true);
            else setIsOpen(false);
        }, 0);
        return () => clearTimeout(timer);
    }, [finished]);

    return (
        <Collapsible open={isOpen} onOpenChange={setIsOpen} className="mb-2 w-full">
            <CollapsibleTrigger asChild>
                <Button variant="ghost" size="sm" className="h-6 w-full justify-start text-xs text-muted-foreground hover:text-foreground gap-1 px-0">
                    {isOpen ? <ChevronDown className="h-3 w-3" /> : <ChevronRight className="h-3 w-3" />}
                    <Brain className="h-3 w-3 text-purple-400" />
                    {finished ? "Processed successfully" : "Reasoning..."}
                </Button>
            </CollapsibleTrigger>
            <CollapsibleContent className="space-y-1 pl-4 border-l-2 border-muted ml-1.5 my-1">
                {steps.map((step, idx) => (
                    <div key={idx} className="text-[10px] text-muted-foreground flex items-center gap-2 animate-in slide-in-from-left-2 fade-in duration-300">
                        <span className="w-1.5 h-1.5 rounded-full bg-purple-500/50" />
                        {step}
                    </div>
                ))}
                {!finished && (
                    <div className="text-[10px] text-purple-400 flex items-center gap-2 animate-pulse">
                        <Loader2 className="h-2.5 w-2.5 animate-spin" />
                        Thinking...
                    </div>
                )}
            </CollapsibleContent>
        </Collapsible>
    );
}

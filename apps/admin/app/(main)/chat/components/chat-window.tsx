"use client";

import { useEffect, useState, useRef } from "react";
import { createApiClient } from "@ec/sdk/client";
import { getAdminMessages, replyToConversation } from "@ec/sdk";
import type { Message } from "@ec/sdk";
import { Loader2, Send, X } from "lucide-react";
import { Button } from "@/components/ui/button";

const client = createApiClient({
  baseUrl: process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000",
});

type ChatWindowProps = {
  conversationId: number;
  onClose: () => void;
};

export function ChatWindow({ conversationId, onClose }: ChatWindowProps) {
  const [messages, setMessages] = useState<Message[]>([]);
  const [loading, setLoading] = useState(true);
  const [sending, setSending] = useState(false);
  const [input, setInput] = useState("");
  const bottomRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    setLoading(true);
    getAdminMessages(client, conversationId)
      .then((res) => setMessages(res.messages))
      .catch(() => {})
      .finally(() => setLoading(false));
  }, [conversationId]);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  async function handleSend() {
    const content = input.trim();
    if (!content || sending) return;
    setSending(true);
    setInput("");
    try {
      const res = await replyToConversation(client, conversationId, content);
      setMessages((prev) => [...prev, res.message]);
    } catch {
      // ignore
    } finally {
      setSending(false);
    }
  }

  function handleKeyDown(e: React.KeyboardEvent<HTMLTextAreaElement>) {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40">
      <div className="flex h-[600px] w-full max-w-lg flex-col rounded-xl bg-white shadow-xl">
        <div className="flex items-center justify-between border-b px-4 py-3">
          <h2 className="text-sm font-medium">对话 #{conversationId}</h2>
          <button onClick={onClose}>
            <X className="size-5 text-muted-foreground hover:text-foreground" />
          </button>
        </div>

        <div className="flex-1 overflow-y-auto px-4 py-4">
          {loading ? (
            <div className="flex items-center justify-center py-12">
              <Loader2 className="size-5 animate-spin text-muted-foreground" />
            </div>
          ) : messages.length === 0 ? (
            <p className="py-12 text-center text-sm text-muted-foreground">
              暂无消息
            </p>
          ) : (
            <div className="space-y-3">
              {messages.map((msg) => (
                <div
                  key={msg.id}
                  className={`flex ${msg.sender === "user" ? "justify-end" : "justify-start"}`}
                >
                  {(() => {
                    const s = msg.sender;
                    const bubbleClass =
                      s === "user"
                        ? "bg-blue-500 text-white rounded-br-sm"
                        : s === "admin"
                          ? "bg-green-50 text-foreground rounded-bl-sm border border-green-200"
                          : "bg-gray-100 text-foreground rounded-bl-sm";
                    return (
                      <div className={`max-w-[80%] rounded-2xl px-3 py-2 text-sm leading-relaxed ${bubbleClass}`}>
                        {s === "admin" && (
                          <span className="mb-1 block text-xs font-medium text-green-600">客服</span>
                        )}
                        {msg.content}
                      </div>
                    );
                  })()}
                </div>
              ))}
              <div ref={bottomRef} />
            </div>
          )}
        </div>

        <div className="flex items-end gap-2 border-t px-4 py-3">
          <textarea
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder="输入回复..."
            rows={1}
            className="flex-1 resize-none rounded-xl border bg-gray-50 px-3 py-2 text-sm outline-none"
          />
          <Button
            size="icon"
            onClick={handleSend}
            disabled={sending || !input.trim()}
          >
            {sending ? (
              <Loader2 className="size-4 animate-spin" />
            ) : (
              <Send className="size-4" />
            )}
          </Button>
        </div>
      </div>
    </div>
  );
}

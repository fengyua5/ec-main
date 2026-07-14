"use client";

import { useEffect, useState } from "react";
import { createApiClient } from "@ec/sdk/client";
import { getAdminConversations } from "@ec/sdk";
import type { AdminConversation } from "@ec/sdk";
import { ChatWindow } from "./components/chat-window";
import { Loader2, MessageSquare } from "lucide-react";

const client = createApiClient({
  baseUrl: process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000",
});

export default function ChatPage() {
  const [conversations, setConversations] = useState<AdminConversation[]>([]);
  const [loading, setLoading] = useState(true);
  const [selectedId, setSelectedId] = useState<number | null>(null);

  useEffect(() => {
    getAdminConversations(client, "waiting_human")
      .then(setConversations)
      .catch(() => {})
      .finally(() => setLoading(false));
  }, []);

  if (loading) {
    return (
      <section className="flex items-center justify-center py-16">
        <Loader2 className="size-6 animate-spin text-muted-foreground" />
      </section>
    );
  }

  return (
    <section className="space-y-6">
      <h1 className="text-2xl font-semibold">客服消息</h1>

      {conversations.length === 0 ? (
        <div className="flex flex-col items-center gap-3 py-16 text-muted-foreground">
          <MessageSquare className="size-10" />
          <p className="text-sm">暂无待处理的对话</p>
        </div>
      ) : (
        <div className="space-y-2">
          {conversations.map((conv) => (
            <button
              key={conv.id}
              onClick={() => setSelectedId(conv.id)}
              className="flex w-full items-center justify-between rounded-lg border px-4 py-3 text-left hover:bg-muted/30"
            >
              <div className="min-w-0 flex-1">
                <p className="text-sm font-medium">
                  对话 #{conv.id}
                  <span className="ml-2 text-xs text-muted-foreground">
                    买家 #{conv.buyer_id}
                  </span>
                </p>
                {conv.last_message && (
                  <p className="mt-1 truncate text-xs text-muted-foreground">
                    {conv.last_message}
                  </p>
                )}
              </div>
              <span className="shrink-0 text-xs text-muted-foreground">
                {new Date(conv.created_at).toLocaleString("zh-CN")}
              </span>
            </button>
          ))}
        </div>
      )}

      {selectedId && (
        <ChatWindow
          conversationId={selectedId}
          onClose={() => setSelectedId(null)}
        />
      )}
    </section>
  );
}

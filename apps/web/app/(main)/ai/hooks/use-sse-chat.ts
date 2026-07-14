"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import { createApiClient } from "@ec/sdk/client";
import {
  chatStream,
  getConversations,
  getMessages,
} from "@ec/sdk";
import type { Message } from "@ec/sdk";

const client = createApiClient({
  baseUrl: process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000",
});

async function* parseSSE(response: Response) {
  const reader = response.body!.getReader();
  const decoder = new TextDecoder();
  let buffer = "";

  while (true) {
    const { done, value } = await reader.read();
    if (done) break;

    buffer += decoder.decode(value, { stream: true });
    const lines = buffer.split("\n");
    buffer = lines.pop() || "";

    for (const line of lines) {
      if (line.startsWith("data: ")) {
        const data = line.slice(6);
        try {
          yield JSON.parse(data);
        } catch {
          // skip malformed JSON
        }
      }
    }
  }
}

export function useSSEChat() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [isStreaming, setIsStreaming] = useState(false);
  const [conversationId, setConversationId] = useState<number | null>(null);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const scrollToBottom = useCallback(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, []);

  useEffect(() => {
    scrollToBottom();
  }, [messages, scrollToBottom]);

  useEffect(() => {
    loadConversation();
  }, []);

  async function loadConversation() {
    try {
      const conversations = await getConversations(client);
      if (conversations.length > 0) {
        const latest = conversations[0];
        setConversationId(latest.id);
        const msgs = await getMessages(client, latest.id);
        setMessages(msgs);
      }
    } catch {
      // no conversations yet
    }
  }

  async function sendMessage(content: string) {
    const userMsg: Message = {
      id: Date.now(),
      conversation_id: conversationId ?? 0,
      sender: "buyer",
      content,
      created_at: new Date().toISOString(),
    };

    setMessages((prev) => [...prev, userMsg]);
    setIsStreaming(true);

    try {
      const response = await chatStream(client, conversationId, content);

      if (!response.ok) {
        throw new Error("Chat request failed");
      }

      const aiMsg: Message = {
        id: Date.now() + 1,
        conversation_id: conversationId ?? 0,
        sender: "ai",
        content: "",
        created_at: new Date().toISOString(),
      };

      setMessages((prev) => [...prev, aiMsg]);

      for await (const event of parseSSE(response)) {
        if (event.type === "token") {
          setMessages((prev) => {
            const updated = [...prev];
            const last = updated[updated.length - 1];
            if (last && last.sender === "ai") {
              updated[updated.length - 1] = { ...last, content: last.content + event.content };
            }
            return updated;
          });
        } else if (event.type === "done") {
          break;
        }
      }
    } catch {
      setMessages((prev) => [
        ...prev,
        {
          id: Date.now() + 2,
          conversation_id: conversationId ?? 0,
          sender: "system",
          content: "消息发送失败，请稍后重试",
          created_at: new Date().toISOString(),
        },
      ]);
    } finally {
      setIsStreaming(false);
    }
  }

  async function loadHistory() {
    if (!conversationId) return;
    try {
      const older = await getMessages(client, conversationId);
      setMessages(older);
    } catch {
      // ignore
    }
  }

  return {
    messages,
    isStreaming,
    sendMessage,
    loadHistory,
    messagesEndRef,
    conversationId,
  };
}

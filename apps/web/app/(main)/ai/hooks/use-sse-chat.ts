"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import { createApiClient, getConversations, getMessages } from "@ec/sdk";
import type { Message } from "@ec/sdk";

const client = createApiClient({
  baseUrl: process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000",
});

type SSEEvent = {
  type: "status" | "intent" | "token" | "done" | "error";
  content?: string;
  value?: unknown;
};

export function useSSEChat() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [isStreaming, setIsStreaming] = useState(false);
  const [conversationId, setConversationId] = useState<number | null>(null);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const workerRef = useRef<Worker | null>(null);
  const streamContentRef = useRef("");
  const streamElRef = useRef<HTMLSpanElement | null>(null);
  const pendingTextRef = useRef<HTMLSpanElement | null>(null);

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
      const { conversations } = await getConversations(client);
      if (conversations.length > 0) {
        const latest = conversations[0];
        setConversationId(latest.id);
        const { messages: msgs } = await getMessages(client, latest.id);
        setMessages(msgs);
      }
    } catch {
      // no conversations yet
    }
  }

  const handleWorkerMessage = useCallback(
    (e: MessageEvent<SSEEvent>) => {
      const event = e.data;

      if (event.type === "status") {
        if (pendingTextRef.current) {
          pendingTextRef.current.textContent = event.content ?? "";
        }
      } else if (event.type === "token") {
        streamContentRef.current += event.content ?? "";
        const el = streamElRef.current;
        if (el) {
          const placeholder = el.parentElement?.querySelector(
            "[data-placeholder]",
          );
          if (placeholder instanceof HTMLElement) {
            placeholder.style.display = "none";
          }
          el.textContent = streamContentRef.current;
          scrollToBottom();
        }
      } else if (event.type === "done") {
        const final = streamContentRef.current;
        streamContentRef.current = "";
        streamElRef.current = null;
        setMessages((prev) => {
          const updated = [...prev];
          const last = updated[updated.length - 1];
          if (last && last.sender === "ai") {
            updated[updated.length - 1] = { ...last, content: final };
          }
          return updated;
        });
        setIsStreaming(false);
      } else if (event.type === "error") {
        streamContentRef.current = "";
        streamElRef.current = null;
        setMessages((prev) => [
          ...prev.filter((m) => !(m.sender === "ai" && !m.content)),
          {
            id: Date.now() + 2,
            conversation_id: conversationId ?? 0,
            sender: "ai" as const,
            content: "消息发送失败，请稍后重试",
            msg_type: "system" as const,
            created_at: new Date().toISOString(),
          },
        ]);
        setIsStreaming(false);
      }
    },
    [scrollToBottom],
  );

  useEffect(() => {
    const worker = new Worker(
      new URL("../workers/ai-chat.worker.ts", import.meta.url),
    );
    workerRef.current = worker;
    worker.onmessage = handleWorkerMessage;
    return () => {
      worker.terminate();
      workerRef.current = null;
    };
  }, [handleWorkerMessage]);

  function sendMessage(content: string) {
    const userMsg: Message = {
      id: Date.now(),
      conversation_id: conversationId ?? 0,
      sender: "user",
      content,
      msg_type: "text",
      created_at: new Date().toISOString(),
    };

    const aiMsg: Message = {
      id: Date.now() + 1,
      conversation_id: conversationId ?? 0,
      sender: "ai",
      content: "",
      msg_type: "text",
      created_at: new Date().toISOString(),
    };

    setMessages((prev) => [...prev, userMsg, aiMsg]);
    setIsStreaming(true);
    streamContentRef.current = "";

    workerRef.current?.postMessage({
      url: `${client.baseUrl}/api/v1/web/ai/chat`,
      payload: { conversation_id: conversationId, content },
    });
  }

  async function loadHistory() {
    if (!conversationId) return;
    try {
      const { messages: msgs } = await getMessages(client, conversationId);
      setMessages(msgs);
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
    contentRef: streamElRef,
    pendingTextRef,
    conversationId,
  };
}

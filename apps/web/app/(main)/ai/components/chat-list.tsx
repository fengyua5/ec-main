"use client";

import type { Message } from "@ec/sdk";
import { MessageBubble } from "./message-bubble";
import { Bot } from "lucide-react";

interface ChatListProps {
  messages: Message[];
  isStreaming: boolean;
  messagesEndRef: React.RefObject<HTMLDivElement | null>;
  onLoadHistory: () => void;
}

export function ChatList({
  messages,
  isStreaming,
  messagesEndRef,
  onLoadHistory,
}: ChatListProps) {
  if (messages.length === 0) {
    return (
      <div className="flex flex-1 flex-col items-center justify-center gap-4 px-4">
        <div className="flex size-16 items-center justify-center rounded-full bg-primary/10">
          <Bot className="size-8 text-primary" />
        </div>
        <div className="text-center">
          <h2 className="text-lg font-semibold">AI 智能客服</h2>
          <p className="mt-1 text-sm text-muted-foreground">
            您好！我是智能客服助手，请问有什么可以帮助您的？
          </p>
        </div>
      </div>
    );
  }

  return (
    <div className="flex-1 overflow-y-auto py-4">
      <button
        onClick={onLoadHistory}
        className="w-full py-2 text-center text-xs text-muted-foreground hover:text-foreground"
      >
        上滑加载更多
      </button>
      {messages.map((msg, i) => (
        <MessageBubble
          key={msg.id ?? i}
          sender={msg.sender}
          content={msg.content}
          isStreaming={isStreaming && i === messages.length - 1 && msg.sender === "ai"}
        />
      ))}
      <div ref={messagesEndRef} />
    </div>
  );
}

"use client";

import { Bot } from "lucide-react";
import { cn } from "@/lib/utils";

interface MessageBubbleProps {
  sender: "buyer" | "ai" | "admin" | "system";
  content: string;
  isStreaming?: boolean;
}

export function MessageBubble({ sender, content, isStreaming }: MessageBubbleProps) {
  if (sender === "system") {
    return (
      <div className="flex justify-center py-2">
        <span className="text-xs text-muted-foreground">{content}</span>
      </div>
    );
  }

  const isBuyer = sender === "buyer";
  const isAdmin = sender === "admin";

  return (
    <div
      className={cn(
        "flex gap-2 px-4 py-1.5",
        isBuyer ? "justify-end" : "justify-start",
      )}
    >
      {!isBuyer && (
        <div className="flex size-8 shrink-0 items-center justify-center rounded-full bg-primary/10">
          {isAdmin ? (
            <span className="text-xs font-medium text-primary">客</span>
          ) : (
            <Bot className="size-4 text-primary" />
          )}
        </div>
      )}
      <div className="flex max-w-[75%] flex-col gap-1">
        {isAdmin && (
          <span className="px-1 text-xs text-green-600 font-medium">客服</span>
        )}
        <div
          className={cn(
            "px-3 py-2 text-sm leading-relaxed",
            isBuyer
              ? "bg-blue-500 text-white rounded-2xl rounded-br-sm"
              : isAdmin
                ? "bg-green-50 text-foreground rounded-2xl rounded-bl-sm border border-green-200"
                : "bg-gray-100 text-foreground rounded-2xl rounded-bl-sm",
          )}
        >
          {content}
          {isStreaming && (
            <span className="ml-0.5 inline-block h-4 w-0.5 animate-pulse bg-current align-text-bottom" />
          )}
        </div>
      </div>
    </div>
  );
}

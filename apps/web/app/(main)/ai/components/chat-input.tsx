"use client";

import { useState, type KeyboardEvent } from "react";
import { Send } from "lucide-react";
import { cn } from "@/lib/utils";

interface ChatInputProps {
  onSend: (content: string) => void;
  disabled?: boolean;
}

export function ChatInput({ onSend, disabled }: ChatInputProps) {
  const [value, setValue] = useState("");

  function handleSend() {
    const trimmed = value.trim();
    if (!trimmed || disabled) return;
    onSend(trimmed);
    setValue("");
  }

  function handleKeyDown(e: KeyboardEvent<HTMLTextAreaElement>) {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  }

  return (
    <div className="border-t bg-white px-4 py-3">
      <div className="flex items-end gap-2 rounded-xl border bg-gray-50 px-3 py-2">
        <textarea
          value={value}
          onChange={(e) => setValue(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder="输入消息..."
          rows={1}
          disabled={disabled}
          className={cn(
            "flex-1 resize-none bg-transparent text-sm outline-none placeholder:text-muted-foreground",
            "disabled:cursor-not-allowed disabled:opacity-50",
          )}
        />
        <button
          onClick={handleSend}
          disabled={disabled || !value.trim()}
          className={cn(
            "flex size-8 shrink-0 items-center justify-center rounded-lg transition-colors",
            value.trim() && !disabled
              ? "bg-blue-500 text-white hover:bg-blue-600"
              : "bg-muted text-muted-foreground",
          )}
        >
          <Send className="size-4" />
        </button>
      </div>
    </div>
  );
}

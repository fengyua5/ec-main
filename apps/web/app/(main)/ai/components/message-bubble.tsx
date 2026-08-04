"use client";

import { Loader2 } from "lucide-react";
import type { Ref } from "react";
import type { Message } from "@ec/sdk";

const senderConfig = {
  user: {
    align: "justify-end",
    bg: "bg-blue-500 text-white",
    rounded: "rounded-2xl rounded-br-sm",
  },
  ai: {
    align: "justify-start",
    bg: "bg-gray-100",
    rounded: "rounded-2xl rounded-bl-sm",
  },
  admin: {
    align: "justify-start",
    bg: "bg-green-100",
    rounded: "rounded-2xl rounded-bl-sm",
  },
} as const;

function RobotIcon() {
  return (
    <div className="flex h-7 w-7 shrink-0 items-center justify-center rounded-full bg-gray-300 text-xs font-bold text-white">
      AI
    </div>
  );
}

type Props = {
  message: Message;
  isStreaming?: boolean;
  contentRef?: Ref<HTMLSpanElement>;
  pendingTextRef?: Ref<HTMLSpanElement>;
};

export function MessageBubble({
  message,
  isStreaming,
  contentRef,
  pendingTextRef,
}: Props) {
  if (message.msg_type === "system") {
    return (
      <div className="flex justify-center py-1">
        <span className="max-w-[80%] break-words rounded-full bg-gray-100 px-3 py-1 text-center text-xs text-gray-500">
          {message.content}
        </span>
      </div>
    );
  }

  type SenderKey = keyof typeof senderConfig;
  const config = senderConfig[message.sender as SenderKey] ?? {
    align: "justify-start",
    bg: "bg-gray-100",
    rounded: "rounded-2xl rounded-bl-sm",
  };

  return (
    <div className={`flex ${config.align} gap-2 px-4 py-1`}>
      {message.sender !== "user" && <RobotIcon />}
      <div
        className={`max-w-[75%] break-words px-3 py-2 text-sm leading-relaxed ${config.bg} ${config.rounded}`}
      >
        <span ref={contentRef}>{message.content}</span>
        {isStreaming && !message.content && (
          <span
            data-placeholder
            className="inline-flex items-center gap-1.5 text-gray-400"
          >
            <Loader2 className="size-3.5 animate-spin" />
            <span ref={pendingTextRef}>正在查找中...</span>
          </span>
        )}
        {isStreaming && message.content && (
          <span className="inline-block w-[2px] animate-pulse bg-blue-500 ml-0.5 h-4 align-text-bottom" />
        )}
      </div>
    </div>
  );
}

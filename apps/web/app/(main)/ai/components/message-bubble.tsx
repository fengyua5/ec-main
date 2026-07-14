"use client";

import type { Message } from "@ec/sdk";

const senderConfig = {
  buyer: {
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
};

export function MessageBubble({ message, isStreaming }: Props) {
  if (message.msg_type === "system") {
    return (
      <div className="flex justify-center py-1">
        <span className="max-w-[80%] break-words rounded-full bg-gray-100 px-3 py-1 text-center text-xs text-gray-500">
          {message.content}
        </span>
      </div>
    );
  }

  const config = senderConfig[message.sender];

  return (
    <div className={`flex ${config.align} gap-2 px-4 py-1`}>
      {message.sender !== "buyer" && <RobotIcon />}
      <div
        className={`max-w-[75%] break-words px-3 py-2 text-sm leading-relaxed ${config.bg} ${config.rounded}`}
      >
        {message.content}
        {isStreaming && (
          <span className="inline-block w-[2px] animate-pulse bg-blue-500 ml-0.5 h-4 align-text-bottom" />
        )}
      </div>
    </div>
  );
}

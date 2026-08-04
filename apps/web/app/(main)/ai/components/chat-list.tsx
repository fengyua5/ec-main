"use client";

import type { Ref } from "react";
import type { Message } from "@ec/sdk";
import { MessageBubble } from "./message-bubble";

type Props = {
  messages: Message[];
  isStreaming: boolean;
  contentRef: Ref<HTMLSpanElement>;
  pendingTextRef: Ref<HTMLSpanElement>;
  messagesEndRef: React.RefObject<HTMLDivElement | null>;
};

export function ChatList({
  messages,
  isStreaming,
  contentRef,
  pendingTextRef,
  messagesEndRef,
}: Props) {
  if (messages.length === 0) {
    return (
      <div className="flex flex-1 items-center justify-center px-4">
        <div className="text-center">
          <div className="mx-auto mb-3 flex h-16 w-16 items-center justify-center rounded-full bg-blue-50">
            <svg
              className="h-8 w-8 text-blue-500"
              fill="none"
              viewBox="0 0 24 24"
              stroke="currentColor"
              strokeWidth={1.5}
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                d="M8.625 12a.375.375 0 11-.75 0 .375.375 0 01.75 0zm0 0H8.25m4.125 0a.375.375 0 11-.75 0 .375.375 0 01.75 0zm0 0H12m4.125 0a.375.375 0 11-.75 0 .375.375 0 01.75 0zm0 0h-.375M21 12c0 4.556-4.03 8.25-9 8.25a9.764 9.764 0 01-2.555-.337A5.972 5.972 0 015.41 20.97a5.969 5.969 0 01-.474-.065 4.48 4.48 0 00.978-2.025c.09-.457-.133-.901-.467-1.226C3.93 16.178 3 14.189 3 12c0-4.556 4.03-8.25 9-8.25s9 3.694 9 8.25z"
              />
            </svg>
          </div>
          <h3 className="text-base font-medium text-gray-700">AI 智能客服</h3>
          <p className="mt-1 text-sm text-gray-500">
            您好！我是 AI 客服助手，有什么可以帮助您的？
          </p>
        </div>
      </div>
    );
  }

  return (
    <div className="flex-1 overflow-y-auto py-3">
      {messages.map((msg, i) => {
        const isStreamingMsg =
          isStreaming && i === messages.length - 1 && msg.sender === "ai";
        return (
          <MessageBubble
            key={msg.id}
            message={msg}
            isStreaming={isStreamingMsg}
            contentRef={isStreamingMsg ? contentRef : undefined}
            pendingTextRef={isStreamingMsg ? pendingTextRef : undefined}
          />
        );
      })}
      <div ref={messagesEndRef} />
    </div>
  );
}

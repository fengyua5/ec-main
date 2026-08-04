"use client";

import { useSSEChat } from "./hooks/use-sse-chat";
import { ChatList } from "./components/chat-list";
import { ChatInput } from "./components/chat-input";

export default function AIChatPage() {
  const {
    messages,
    isStreaming,
    sendMessage,
    messagesEndRef,
    contentRef,
    pendingTextRef,
  } = useSSEChat();

  return (
    <div className="flex h-[calc(100dvh-4rem)] flex-col">
      <div className="border-b px-4 py-3 text-center font-semibold shrink-0">
        AI 智能客服
      </div>
      <ChatList
        messages={messages}
        isStreaming={isStreaming}
        contentRef={contentRef}
        pendingTextRef={pendingTextRef}
        messagesEndRef={messagesEndRef}
      />
      <ChatInput onSend={sendMessage} disabled={isStreaming} />
    </div>
  );
}

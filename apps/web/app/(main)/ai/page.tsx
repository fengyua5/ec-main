"use client";

import { useSSEChat } from "./hooks/use-sse-chat";
import { ChatList } from "./components/chat-list";
import { ChatInput } from "./components/chat-input";

export default function AIChatPage() {
  const { messages, isStreaming, sendMessage, loadHistory, messagesEndRef } =
    useSSEChat();

  return (
    <div className="flex h-[calc(100dvh-4rem)] flex-col">
      <div className="border-b px-4 py-3 text-center font-semibold">
        AI 智能客服
      </div>
      <ChatList
        messages={messages}
        isStreaming={isStreaming}
        messagesEndRef={messagesEndRef}
        onLoadHistory={loadHistory}
      />
      <ChatInput onSend={sendMessage} disabled={isStreaming} />
    </div>
  );
}

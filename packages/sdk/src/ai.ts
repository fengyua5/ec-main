import type { ApiClient } from "./client";

export type Message = {
  id: number;
  conversation_id: number;
  sender: "buyer" | "ai" | "admin" | "system";
  content: string;
  created_at: string;
};

export type Conversation = {
  id: number;
  title: string;
  created_at: string;
  updated_at: string;
};

export function chatStream(
  client: ApiClient,
  conversationId: number | null,
  content: string,
): Promise<Response> {
  return fetch(`${client.baseUrl}/api/v1/web/ai/chat/stream`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ conversation_id: conversationId, content }),
    credentials: "include",
  });
}

export function getConversations(client: ApiClient): Promise<Conversation[]> {
  return client.request<Conversation[]>("/api/v1/web/ai/conversations");
}

export function getMessages(
  client: ApiClient,
  conversationId: number,
): Promise<Message[]> {
  return client.request<Message[]>(
    `/api/v1/web/ai/conversations/${conversationId}/messages`,
  );
}

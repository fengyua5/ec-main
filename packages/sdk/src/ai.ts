import type { ApiClient } from "./client";

export type Conversation = {
  id: number;
  buyer_id: number;
  status: string;
  created_at: string;
  updated_at: string;
};

export type Message = {
  id: number;
  conversation_id: number;
  sender: "user" | "ai" | "admin" | "system";
  content: string;
  msg_type: "text" | "system" | "refund_info";
  created_at: string;
};

export type FAQDocument = {
  id: number;
  filename: string;
  chunk_count: number;
  created_at: string;
};

export type ChatResponse = {
  conversation_id: number;
  messages: Message[];
};

export type ConversationsResponse = {
  conversations: Conversation[];
};

export type MessagesResponse = {
  messages: Message[];
};

export type FAQDocumentsResponse = {
  documents: FAQDocument[];
};

export type DeleteResponse = {
  success: boolean;
  error?: string;
};

/**
 * Send a chat message via SSE streaming.
 * Returns the Response object for manual stream reading.
 */
export function chatStream(
  client: ApiClient,
  data: { conversation_id?: number | null; content: string },
): Promise<Response> {
  const url = `${client.baseUrl}/api/v1/web/ai/chat`;
  return fetch(url, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    credentials: "include",
    body: JSON.stringify(data),
  });
}

/** Get conversations for current buyer */
export function getConversations(
  client: ApiClient,
): Promise<ConversationsResponse> {
  return client.request<ConversationsResponse>(`/api/v1/web/ai/conversations`);
}

/** Get messages for a conversation */
export function getMessages(
  client: ApiClient,
  conversationId: number,
  params?: { limit?: number; offset?: number },
): Promise<MessagesResponse> {
  const query = new URLSearchParams();
  if (params?.limit) query.set("limit", String(params.limit));
  if (params?.offset) query.set("offset", String(params.offset));
  const qs = query.toString();
  return client.request<MessagesResponse>(
    `/api/v1/web/ai/conversations/${conversationId}/messages${qs ? `?${qs}` : ""}`,
  );
}

/** Upload a FAQ document (Admin) */
export function uploadFAQDocument(
  client: ApiClient,
  file: File,
): Promise<FAQDocument> {
  const formData = new FormData();
  formData.append("file", file);
  const url = `${client.baseUrl}/api/v1/admin/ai/faq/upload`;
  return fetch(url, {
    method: "POST",
    body: formData,
    credentials: "include",
  }).then((r) => r.json());
}

/** List FAQ documents (Admin) */
export function getFAQDocuments(
  client: ApiClient,
): Promise<FAQDocumentsResponse> {
  return client.request<FAQDocumentsResponse>(`/api/v1/admin/ai/faq/documents`);
}

/** Delete a FAQ document (Admin) */
export function deleteFAQDocument(
  client: ApiClient,
  documentId: number,
): Promise<DeleteResponse> {
  return client.request<DeleteResponse>(
    `/api/v1/admin/ai/faq/documents/${documentId}`,
    { method: "DELETE" },
  );
}

/** List all conversations (Admin) */
export function getAdminConversations(
  client: ApiClient,
  status?: string,
): Promise<ConversationsResponse> {
  const query = status ? `?status=${status}` : "";
  return client.request<ConversationsResponse>(
    `/api/v1/admin/ai/conversations${query}`,
  );
}

/** Get messages for a conversation (Admin) */
export function getAdminMessages(
  client: ApiClient,
  conversationId: number,
): Promise<MessagesResponse> {
  return client.request<MessagesResponse>(
    `/api/v1/admin/ai/conversations/${conversationId}/messages`,
  );
}

/** Admin reply to a conversation */
export function replyToConversation(
  client: ApiClient,
  conversationId: number,
  content: string,
): Promise<{ message: Message }> {
  return client.request<{ message: Message }>(
    `/api/v1/admin/ai/conversations/${conversationId}/reply`,
    {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ content }),
    },
  );
}

/** Close a conversation (triggers memory extraction) */
export function closeConversation(
  client: ApiClient,
  conversationId: number,
): Promise<{ id: number; status: string }> {
  return client.request<{ id: number; status: string }>(
    `/api/v1/web/ai/conversations/${conversationId}/close`,
    { method: "POST" },
  );
}

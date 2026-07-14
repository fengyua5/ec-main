import type { ApiClient } from "./client";
import type { Message } from "./ai";

export type FAQDocument = {
  id: number;
  filename: string;
  chunk_count: number;
  created_at: string;
};

export type AdminConversation = {
  id: number;
  buyer_id: number;
  status: string;
  last_message: string | null;
  created_at: string;
  updated_at: string;
};

export function getFAQDocuments(client: ApiClient): Promise<FAQDocument[]> {
  return client.request<FAQDocument[]>("/api/v1/admin/faq/documents");
}

export function uploadFAQDocument(client: ApiClient, file: File): Promise<FAQDocument> {
  const formData = new FormData();
  formData.append("file", file);
  return fetch(`${client.baseUrl}/api/v1/admin/faq/documents`, {
    method: "POST",
    body: formData,
    credentials: "include",
  }).then((res) => {
    if (!res.ok) throw new Error("Upload failed");
    return res.json();
  });
}

export function deleteFAQDocument(client: ApiClient, id: number): Promise<void> {
  return client.request<void>(`/api/v1/admin/faq/documents/${id}`, {
    method: "DELETE",
  });
}

export function getAdminConversations(client: ApiClient, status?: string): Promise<AdminConversation[]> {
  const params = status ? `?status=${encodeURIComponent(status)}` : "";
  return client.request<AdminConversation[]>(`/api/v1/admin/ai/conversations${params}`);
}

export function getAdminMessages(client: ApiClient, conversationId: number): Promise<Message[]> {
  return client.request<Message[]>(`/api/v1/admin/ai/conversations/${conversationId}/messages`);
}

export function replyToConversation(client: ApiClient, conversationId: number, content: string): Promise<Message> {
  return client.request<Message>(`/api/v1/admin/ai/conversations/${conversationId}/reply`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ content }),
  });
}

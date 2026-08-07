import type { ApiClient } from "./client";

export type AdminUser = {
  id: number;
  username: string | null;
  email: string;
  role: string;
  is_active: boolean;
  created_at: string;
};

export type UserListResponse = {
  items: AdminUser[];
  total: number;
  page: number;
  page_size: number;
};

export type UserStatusFilter = "active" | "inactive";

export function getUsers(
  client: ApiClient,
  options?: { page?: number; page_size?: number; keyword?: string; status?: UserStatusFilter },
): Promise<UserListResponse> {
  const params = new URLSearchParams();
  if (options?.page) params.set("page", String(options.page));
  if (options?.page_size) params.set("page_size", String(options.page_size));
  if (options?.keyword) params.set("keyword", options.keyword);
  if (options?.status) params.set("status", options.status);
  const query = params.toString();
  return client.request<UserListResponse>(`/api/v1/admin/users${query ? `?${query}` : ""}`);
}

export function getUser(client: ApiClient, userId: number): Promise<AdminUser> {
  return client.request<AdminUser>(`/api/v1/admin/users/${userId}`);
}

export function setUserActive(
  client: ApiClient,
  userId: number,
  isActive: boolean,
): Promise<{ user: AdminUser }> {
  return client.request<{ user: AdminUser }>(`/api/v1/admin/users/${userId}/active`, {
    method: "PATCH",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ is_active: isActive }),
  });
}

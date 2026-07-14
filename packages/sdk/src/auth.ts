import type { ApiClient } from "./client";

export type UserResponse = {
  id: number;
  username: string | null;
  email: string;
  role: "buyer" | "admin";
  created_at: string;
};

export type AuthResponse = {
  user: UserResponse;
};

export type RegisterRequest = {
  username?: string;
  email: string;
  password: string;
};

export type LoginRequest = {
  email: string;
  password: string;
};

export function register(
  client: ApiClient,
  path: "/web" | "/admin",
  data: RegisterRequest,
): Promise<AuthResponse> {
  return client.request<AuthResponse>(`/api/v1${path}/auth/register`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(data),
  });
}

export function login(
  client: ApiClient,
  path: "/web" | "/admin",
  data: LoginRequest,
): Promise<AuthResponse> {
  return client.request<AuthResponse>(`/api/v1${path}/auth/login`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(data),
  });
}

export function logout(
  client: ApiClient,
  path: "/web" | "/admin",
): Promise<{ message: string }> {
  return client.request<{ message: string }>(`/api/v1${path}/auth/logout`, {
    method: "POST",
  });
}

export function getMe(
  client: ApiClient,
  path: "/web" | "/admin",
): Promise<UserResponse> {
  return client.request<UserResponse>(`/api/v1${path}/auth/me`, {
    method: "GET",
  });
}

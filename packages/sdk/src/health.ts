import type { ApiClient } from "./client";

export type HealthResponse = {
  status: "ok";
  service: "ec-backend";
};

export function checkHealth(client: ApiClient): Promise<HealthResponse> {
  return client.request<HealthResponse>("/health");
}

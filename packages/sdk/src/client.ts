export type ApiClient = {
  baseUrl: string;
  request<T>(path: string, init?: RequestInit): Promise<T>;
};

export function createApiClient(options: { baseUrl: string }): ApiClient {
  const baseUrl = options.baseUrl.replace(/\/$/, "");

  return {
    baseUrl,
    async request<T>(path: string, init?: RequestInit) {
      const response = await fetch(`${baseUrl}${path}`, init);

      if (!response.ok) {
        throw new Error(`API request failed: ${response.status} ${response.statusText}`);
      }

      return response.json() as Promise<T>;
    }
  };
}

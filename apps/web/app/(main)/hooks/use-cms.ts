"use client";

import { useState, useEffect, useCallback } from "react";
import { createApiClient } from "@ec/sdk/client";

const client = createApiClient({
  baseUrl: process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000",
});

export function useCMS<T = unknown>(
  module: { is_static: boolean; data_source_url: string },
  initialData?: T,
) {
  const [data, setData] = useState<T | null>(initialData ?? null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const loadData = useCallback(async () => {
    if (module.is_static || !module.data_source_url) return;
    setLoading(true);
    setError(null);
    try {
      const result = await client.request<T>(module.data_source_url);
      setData(result);
    } catch {
      setError("数据加载失败");
    } finally {
      setLoading(false);
    }
  }, [module.is_static, module.data_source_url]);

  useEffect(() => {
    if (!module.is_static && module.data_source_url) {
      void loadData();
    }
  }, [loadData, module.is_static, module.data_source_url]);

  return { data, loading, error };
}
"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { createApiClient, register } from "@ec/sdk";
import { Button } from "@ec/ui";

const client = createApiClient({
  baseUrl: process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000",
});

export default function RegisterPage() {
  const router = useRouter();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError(null);
    try {
      await register(client, "/web", { email, password });
      router.push("/");
    } catch (err) {
      setError(err instanceof Error ? err.message : "注册失败");
    }
  }

  return (
    <div className="mx-auto mt-16 max-w-md">
      <h1 className="mb-6 text-2xl font-bold">注册买家账号</h1>
      <form onSubmit={handleSubmit} className="space-y-4">
        <div>
          <label className="mb-1 block text-sm font-medium">邮箱</label>
          <input
            type="email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            required
            className="w-full rounded border px-3 py-2"
          />
        </div>
        <div>
          <label className="mb-1 block text-sm font-medium">密码</label>
          <input
            type="password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            required
            className="w-full rounded border px-3 py-2"
          />
        </div>
        {error && <p className="text-sm text-red-600">{error}</p>}
        <Button type="submit" variant="primary" className="w-full">
          注册
        </Button>
        <p className="text-sm text-gray-500">
          已有账号？<a href="/login" className="text-blue-600 hover:underline">去登录</a>
        </p>
      </form>
    </div>
  );
}

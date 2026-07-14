"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { createApiClient, getMe, logout } from "@ec/sdk";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";

type User = {
  id: number;
  username: string | null;
  email: string;
  role: string;
  created_at: string;
};

const client = createApiClient({
  baseUrl: process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000",
});

export default function AccountPage() {
  const router = useRouter();
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    getMe(client, "/web")
      .then(setUser)
      .catch(() => setUser(null))
      .finally(() => setLoading(false));
  }, []);

  async function handleLogout() {
    await logout(client, "/web");
    setUser(null);
    router.push("/login");
  }

  if (loading) {
    return (
      <div className="flex min-h-[60vh] items-center justify-center">
        <p className="text-muted-foreground">加载中...</p>
      </div>
    );
  }

  if (!user) {
    return (
      <div className="flex min-h-[60vh] flex-col items-center justify-center gap-6">
        <div className="text-center space-y-2">
          <h1 className="text-2xl font-semibold">未登录</h1>
          <p className="text-muted-foreground">请登录后查看账号信息</p>
        </div>
        <div className="flex gap-4">
          <a href="/login">
            <Button variant="outline">登录</Button>
          </a>
          <a href="/register">
            <Button>注册</Button>
          </a>
        </div>
      </div>
    );
  }

  return (
    <div className="flex min-h-[60vh] flex-col items-center justify-center gap-6">
      <Card className="w-full max-w-sm">
        <CardHeader>
          <CardTitle className="text-center">账号信息</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="space-y-1">
            <p className="text-sm text-muted-foreground">用户名</p>
            <p className="font-medium">{user.username ?? "（未设置）"}</p>
          </div>
          <div className="space-y-1">
            <p className="text-sm text-muted-foreground">邮箱</p>
            <p className="font-medium">{user.email}</p>
          </div>
          <div className="space-y-1">
            <p className="text-sm text-muted-foreground">角色</p>
            <p className="font-medium">角色: {user.role}</p>
          </div>
          <Button onClick={handleLogout} variant="outline" className="w-full">
            登出
          </Button>
        </CardContent>
      </Card>
    </div>
  );
}

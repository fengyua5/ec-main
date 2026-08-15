"use client";

import { useEffect, useState, useCallback } from "react";
import { createApiClient } from "@ec/sdk/client";
import { getUsers, setUserActive } from "@ec/sdk";
import type { AdminUser, UserStatusFilter } from "@ec/sdk";
import { Loader2, Search } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";

const client = createApiClient({
  baseUrl: process.env.NEXT_PUBLIC_API_URL || "",
});

const PAGE_SIZE = 20;

function RoleBadge({ role }: { role: string }) {
  const isAdmin = role === "admin";
  return (
    <span
      className={`inline-block rounded-full px-2.5 py-0.5 text-xs ${
        isAdmin ? "bg-purple-100 text-purple-800" : "bg-gray-100 text-gray-700"
      }`}
    >
      {isAdmin ? "管理员" : "买家"}
    </span>
  );
}

function StatusBadge({ active }: { active: boolean }) {
  return (
    <span
      className={`inline-block rounded-full px-2.5 py-0.5 text-xs ${
        active ? "bg-green-100 text-green-800" : "bg-red-100 text-red-800"
      }`}
    >
      {active ? "正常" : "已禁用"}
    </span>
  );
}

export default function UsersPage() {
  const [users, setUsers] = useState<AdminUser[]>([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [keyword, setKeyword] = useState("");
  const [status, setStatus] = useState<UserStatusFilter | "all">("all");
  const [currentUserId, setCurrentUserId] = useState<number | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [feedback, setFeedback] = useState<{
    type: "success" | "error";
    message: string;
  } | null>(null);
  const [togglingId, setTogglingId] = useState<number | null>(null);

  useEffect(() => {
    fetch("/api/auth/me")
      .then((res) => (res.ok ? res.json() : null))
      .then((data) => setCurrentUserId(data?.id ?? null))
      .catch(() => setCurrentUserId(null));
  }, []);

  const loadUsers = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await getUsers(client, {
        page,
        page_size: PAGE_SIZE,
        keyword: keyword || undefined,
        status: status === "all" ? undefined : status,
      });
      setUsers(res.items);
      setTotal(res.total);
    } catch {
      setError("加载用户列表失败");
    } finally {
      setLoading(false);
    }
  }, [page, keyword, status]);

  useEffect(() => {
    loadUsers();
  }, [loadUsers]);

  function handleSearch() {
    setPage(1);
    loadUsers();
  }

  async function handleToggle(user: AdminUser) {
    const next = !user.is_active;
    if (next === false && !confirm(`确定要禁用用户 ${user.email} 吗？`)) return;
    setTogglingId(user.id);
    setFeedback(null);
    try {
      const res = await setUserActive(client, user.id, next);
      setUsers((prev) => prev.map((u) => (u.id === user.id ? res.user : u)));
      setFeedback({ type: "success", message: `${next ? "启用" : "禁用"}成功` });
    } catch {
      setFeedback({ type: "error", message: "操作失败" });
    } finally {
      setTogglingId(null);
    }
  }

  const totalPages = Math.max(1, Math.ceil(total / PAGE_SIZE));

  return (
    <section className="space-y-6">
      <h1 className="text-2xl font-semibold">用户管理</h1>

      <div className="flex flex-wrap items-center gap-3">
        <select
          value={status}
          onChange={(e) => {
            setStatus(e.target.value as UserStatusFilter | "all");
            setPage(1);
          }}
          className="h-8 rounded-lg border border-input bg-transparent px-2.5 text-sm outline-none focus-visible:border-ring focus-visible:ring-3 focus-visible:ring-ring/50"
        >
          <option value="all">全部状态</option>
          <option value="active">正常</option>
          <option value="inactive">已禁用</option>
        </select>

        <div className="flex items-center gap-2">
          <div className="relative">
            <Search className="absolute left-2.5 top-1/2 size-4 -translate-y-1/2 text-muted-foreground" />
            <Input
              value={keyword}
              onChange={(e) => setKeyword(e.target.value)}
              onKeyDown={(e) => {
                if (e.key === "Enter") handleSearch();
              }}
              placeholder="搜索邮箱/用户名..."
              className="pl-8"
            />
          </div>
          <Button onClick={handleSearch}>搜索</Button>
        </div>
      </div>

      {feedback && (
        <p
          className={`text-sm ${feedback.type === "success" ? "text-green-600" : "text-red-600"}`}
        >
          {feedback.message}
        </p>
      )}
      {error && <p className="text-sm text-red-600">{error}</p>}

      {loading ? (
        <div className="flex items-center justify-center py-12">
          <Loader2 className="size-6 animate-spin text-muted-foreground" />
        </div>
      ) : users.length === 0 ? (
        <p className="py-8 text-center text-sm text-muted-foreground">暂无用户</p>
      ) : (
        <div className="overflow-hidden rounded-lg border">
          <table className="w-full text-sm">
            <thead className="bg-muted/50">
              <tr>
                <th className="px-4 py-3 text-left font-medium">ID</th>
                <th className="px-4 py-3 text-left font-medium">用户名</th>
                <th className="px-4 py-3 text-left font-medium">邮箱</th>
                <th className="px-4 py-3 text-left font-medium">角色</th>
                <th className="px-4 py-3 text-left font-medium">状态</th>
                <th className="px-4 py-3 text-left font-medium">注册时间</th>
                <th className="px-4 py-3 text-right font-medium">操作</th>
              </tr>
            </thead>
            <tbody className="divide-y">
              {users.map((user) => (
                <tr key={user.id} className="hover:bg-muted/30">
                  <td className="px-4 py-3">{user.id}</td>
                  <td className="px-4 py-3">{user.username ?? "—"}</td>
                  <td className="px-4 py-3">{user.email}</td>
                  <td className="px-4 py-3">
                    <RoleBadge role={user.role} />
                  </td>
                  <td className="px-4 py-3">
                    <StatusBadge active={user.is_active} />
                  </td>
                  <td className="px-4 py-3">
                    {new Date(user.created_at).toLocaleString("zh-CN")}
                  </td>
                  <td className="px-4 py-3 text-right">
                    {user.role === "admin" && user.id === currentUserId ? (
                      <span className="text-xs text-muted-foreground">当前账号</span>
                    ) : (
                      <Button
                        variant={user.is_active ? "destructive" : "outline"}
                        size="sm"
                        disabled={togglingId === user.id}
                        onClick={() => handleToggle(user)}
                      >
                        {togglingId === user.id ? (
                          <Loader2 className="size-4 animate-spin" />
                        ) : user.is_active ? (
                          "禁用"
                        ) : (
                          "启用"
                        )}
                      </Button>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {!loading && users.length > 0 && (
        <div className="flex items-center justify-between text-sm text-muted-foreground">
          <span>
            共 {total} 条，第 {page} / {totalPages} 页
          </span>
          <div className="flex items-center gap-2">
            <Button
              variant="outline"
              size="sm"
              disabled={page <= 1}
              onClick={() => setPage((p) => p - 1)}
            >
              上一页
            </Button>
            <Button
              variant="outline"
              size="sm"
              disabled={page >= totalPages}
              onClick={() => setPage((p) => p + 1)}
            >
              下一页
            </Button>
          </div>
        </div>
      )}
    </section>
  );
}

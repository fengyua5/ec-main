"use client";

import { useEffect, useState, useCallback } from "react";
import { createApiClient } from "@ec/sdk/client";
import { getOrders } from "@ec/sdk";
import type { Order, OrderStatus } from "@ec/sdk";
import { Loader2, Search } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import {
  ORDER_STATUS_LABELS,
  ORDER_STATUS_COLORS,
} from "./order-constants";

const client = createApiClient({
  baseUrl: process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000",
});

const ALL_STATUSES: (OrderStatus | "all")[] = [
  "all",
  "pending_payment",
  "pending_delivery",
  "in_delivery",
  "delivered",
  "cancelled",
  "refunded",
];

const PAGE_SIZE = 20;

export default function OrdersPage() {
  const [orders, setOrders] = useState<Order[]>([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [status, setStatus] = useState<OrderStatus | "all">("all");
  const [keyword, setKeyword] = useState("");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const loadOrders = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await getOrders(client, {
        page,
        page_size: PAGE_SIZE,
        status: status === "all" ? undefined : status,
        keyword: keyword || undefined,
      });
      setOrders(res.items);
      setTotal(res.total);
    } catch {
      setError("加载订单列表失败");
    } finally {
      setLoading(false);
    }
  }, [page, status, keyword]);

  useEffect(() => {
    loadOrders();
  }, [loadOrders]);

  function handleSearch() {
    setPage(1);
    loadOrders();
  }

  const totalPages = Math.max(1, Math.ceil(total / PAGE_SIZE));

  return (
    <section className="space-y-6">
      <h1 className="text-2xl font-semibold">订单管理</h1>

      <div className="flex flex-wrap items-center gap-3">
        <select
          value={status}
          onChange={(e) => {
            setStatus(e.target.value as OrderStatus | "all");
            setPage(1);
          }}
          className="h-8 rounded-lg border border-input bg-transparent px-2.5 text-sm outline-none focus-visible:border-ring focus-visible:ring-3 focus-visible:ring-ring/50"
        >
          {ALL_STATUSES.map((s) => (
            <option key={s} value={s}>
              {s === "all" ? "全部状态" : ORDER_STATUS_LABELS[s as OrderStatus]}
            </option>
          ))}
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
              placeholder="搜索订单号..."
              className="pl-8"
            />
          </div>
          <Button onClick={handleSearch}>搜索</Button>
        </div>
      </div>

      {error && <p className="text-sm text-red-600">{error}</p>}

      {loading ? (
        <div className="flex items-center justify-center py-12">
          <Loader2 className="size-6 animate-spin text-muted-foreground" />
        </div>
      ) : orders.length === 0 ? (
        <p className="py-8 text-center text-sm text-muted-foreground">
          暂无订单
        </p>
      ) : (
        <div className="overflow-hidden rounded-lg border">
          <table className="w-full text-sm">
            <thead className="bg-muted/50">
              <tr>
                <th className="px-4 py-3 text-left font-medium">订单号</th>
                <th className="px-4 py-3 text-left font-medium">买家 ID</th>
                <th className="px-4 py-3 text-left font-medium">金额</th>
                <th className="px-4 py-3 text-left font-medium">状态</th>
                <th className="px-4 py-3 text-left font-medium">创建时间</th>
                <th className="px-4 py-3 text-right font-medium">操作</th>
              </tr>
            </thead>
            <tbody className="divide-y">
              {orders.map((order) => (
                <tr key={order.order_no} className="hover:bg-muted/30">
                  <td className="px-4 py-3 font-medium">{order.order_no}</td>
                  <td className="px-4 py-3">{order.buyer_id}</td>
                  <td className="px-4 py-3">¥{order.amount}</td>
                  <td className="px-4 py-3">
                    <span
                      className={`inline-block rounded-full px-2.5 py-0.5 text-xs ${ORDER_STATUS_COLORS[order.status]}`}
                    >
                      {ORDER_STATUS_LABELS[order.status]}
                    </span>
                  </td>
                  <td className="px-4 py-3">
                    {new Date(order.created_at).toLocaleString("zh-CN")}
                  </td>
                  <td className="px-4 py-3 text-right">
                    <a
                      href={`/orders/${order.order_no}`}
                      className="text-sm text-blue-600 hover:underline"
                    >
                      查看详情
                    </a>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {!loading && orders.length > 0 && (
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

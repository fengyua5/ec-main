"use client";

import { useEffect, useState } from "react";
import { useParams } from "next/navigation";
import { createApiClient } from "@ec/sdk/client";
import { getOrder, updateOrderStatus } from "@ec/sdk";
import type { Order, OrderStatus } from "@ec/sdk";
import { Loader2, ArrowLeft } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import {
  ORDER_STATUS_LABELS,
  ORDER_STATUS_COLORS,
  getNextStatuses,
} from "../order-constants";

const client = createApiClient({
  baseUrl: process.env.NEXT_PUBLIC_API_URL || "",
});

export default function OrderDetailPage() {
  const params = useParams<{ order_no: string }>();
  const orderNo = params.order_no;

  const [order, setOrder] = useState<Order | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [updating, setUpdating] = useState(false);
  const [feedback, setFeedback] = useState<{
    type: "success" | "error";
    message: string;
  } | null>(null);

  useEffect(() => {
    setLoading(true);
    setError(null);
    getOrder(client, orderNo)
      .then((res) => setOrder(res))
      .catch(() => setError("加载订单失败或订单不存在"))
      .finally(() => setLoading(false));
  }, [orderNo]);

  async function handleUpdateStatus(target: OrderStatus) {
    if (!order) return;
    setUpdating(true);
    setFeedback(null);
    try {
      const res = await updateOrderStatus(client, order.order_no, target);
      setOrder(res.order);
      setFeedback({ type: "success", message: "状态修改成功" });
    } catch {
      setFeedback({ type: "error", message: "状态修改失败" });
    } finally {
      setUpdating(false);
    }
  }

  if (loading) {
    return (
      <section className="flex items-center justify-center py-16">
        <Loader2 className="size-6 animate-spin text-muted-foreground" />
      </section>
    );
  }

  if (error || !order) {
    return (
      <section className="space-y-4 py-8">
        <a href="/orders" className="inline-flex items-center gap-1 text-sm text-blue-600 hover:underline">
          <ArrowLeft className="size-4" />
          返回订单列表
        </a>
        <p className="text-sm text-red-600">{error}</p>
      </section>
    );
  }

  const nextStatuses = getNextStatuses(order.status);

  return (
    <section className="space-y-6">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <a href="/orders" className="text-muted-foreground hover:text-foreground">
            <ArrowLeft className="size-5" />
          </a>
          <h1 className="text-2xl font-semibold">订单 {order.order_no}</h1>
          <span
            className={`inline-block rounded-full px-2.5 py-0.5 text-xs ${ORDER_STATUS_COLORS[order.status]}`}
          >
            {ORDER_STATUS_LABELS[order.status]}
          </span>
        </div>
      </div>

      {feedback && (
        <p
          className={`text-sm ${feedback.type === "success" ? "text-green-600" : "text-red-600"}`}
        >
          {feedback.message}
        </p>
      )}

      <Card>
        <CardHeader>
          <CardTitle>订单信息</CardTitle>
        </CardHeader>
        <CardContent>
          <dl className="grid grid-cols-2 gap-4 sm:grid-cols-3">
            <div>
              <dt className="text-xs text-muted-foreground">订单号</dt>
              <dd className="mt-1 text-sm font-medium">{order.order_no}</dd>
            </div>
            <div>
              <dt className="text-xs text-muted-foreground">买家 ID</dt>
              <dd className="mt-1 text-sm font-medium">{order.buyer_id}</dd>
            </div>
            <div>
              <dt className="text-xs text-muted-foreground">金额</dt>
              <dd className="mt-1 text-sm font-medium">¥{order.amount}</dd>
            </div>
            <div>
              <dt className="text-xs text-muted-foreground">当前状态</dt>
              <dd className="mt-1 text-sm font-medium">
                {ORDER_STATUS_LABELS[order.status]}
              </dd>
            </div>
            <div>
              <dt className="text-xs text-muted-foreground">创建时间</dt>
              <dd className="mt-1 text-sm font-medium">
                {new Date(order.created_at).toLocaleString("zh-CN")}
              </dd>
            </div>
          </dl>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>修改订单状态</CardTitle>
        </CardHeader>
        <CardContent>
          {nextStatuses.length === 0 ? (
            <p className="text-sm text-muted-foreground">
              当前状态为终态，不可再修改。
            </p>
          ) : (
            <div className="flex flex-wrap items-center gap-2">
              {nextStatuses.map((target) => (
                <Button
                  key={target}
                  variant="outline"
                  disabled={updating}
                  onClick={() => handleUpdateStatus(target)}
                >
                  {updating ? (
                    <Loader2 className="size-4 animate-spin" />
                  ) : null}
                  变更为 {ORDER_STATUS_LABELS[target]}
                </Button>
              ))}
            </div>
          )}
        </CardContent>
      </Card>
    </section>
  );
}

import type { ApiClient } from "./client";

export type OrderStatus =
  | "pending_payment"
  | "pending_delivery"
  | "in_delivery"
  | "delivered"
  | "cancelled"
  | "refunded";

export type Order = {
  order_no: string;
  buyer_id: number;
  amount: string;
  status: OrderStatus;
  created_at: string;
};

export type OrderListResponse = {
  items: Order[];
  total: number;
  page: number;
  page_size: number;
};

export function getOrders(
  client: ApiClient,
  options?: { page?: number; page_size?: number; status?: OrderStatus; keyword?: string },
): Promise<OrderListResponse> {
  const params = new URLSearchParams();
  if (options?.page) params.set("page", String(options.page));
  if (options?.page_size) params.set("page_size", String(options.page_size));
  if (options?.status) params.set("status", options.status);
  if (options?.keyword) params.set("keyword", options.keyword);
  const query = params.toString();
  return client.request<OrderListResponse>(`/api/v1/admin/orders${query ? `?${query}` : ""}`);
}

export function getOrder(client: ApiClient, orderNo: string): Promise<Order> {
  return client.request<Order>(`/api/v1/admin/orders/${encodeURIComponent(orderNo)}`);
}

export function updateOrderStatus(
  client: ApiClient,
  orderNo: string,
  status: OrderStatus,
): Promise<{ order: Order }> {
  return client.request<{ order: Order }>(`/api/v1/admin/orders/${encodeURIComponent(orderNo)}/status`, {
    method: "PATCH",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ status }),
  });
}

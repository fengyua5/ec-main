import type { OrderStatus } from "@ec/sdk";

export const ORDER_STATUS_LABELS: Record<OrderStatus, string> = {
  pending_payment: "待付款",
  pending_delivery: "待发货",
  in_delivery: "配送中",
  delivered: "已送达",
  cancelled: "已取消",
  refunded: "已退款",
};

export const ORDER_STATUS_COLORS: Record<OrderStatus, string> = {
  pending_payment: "bg-yellow-100 text-yellow-800",
  pending_delivery: "bg-blue-100 text-blue-800",
  in_delivery: "bg-purple-100 text-purple-800",
  delivered: "bg-green-100 text-green-800",
  cancelled: "bg-gray-200 text-gray-700",
  refunded: "bg-orange-100 text-orange-800",
};

export const ORDER_TRANSITIONS: Partial<Record<OrderStatus, OrderStatus[]>> = {
  pending_payment: ["pending_delivery", "cancelled"],
  pending_delivery: ["in_delivery", "cancelled", "refunded"],
  in_delivery: ["delivered"],
};

export function getNextStatuses(current: OrderStatus): OrderStatus[] {
  return ORDER_TRANSITIONS[current] ?? [];
}

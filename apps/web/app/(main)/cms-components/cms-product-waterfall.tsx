import type { Product } from "@ec/sdk";
import { CmsTitle } from "./cms-title";

type Props = {
  title?: string;
  items: Product[];
  onLoadMore?: () => void;
  hasMore?: boolean;
  loading?: boolean;
};

export function formatPrice(cents: number): string {
  return `¥${(cents / 100).toFixed(2)}`;
}

export function CmsProductWaterfall({ title, items, onLoadMore, hasMore, loading }: Props) {
  if (items.length === 0) return null;
  return (
    <div>
      {title && <CmsTitle title={title} />}
      <div className="grid grid-cols-2 gap-3 px-3 pt-3 sm:grid-cols-3 lg:grid-cols-4">
        {items.map((product) => (
          <div
            key={product.id}
            className="overflow-hidden rounded-xl border bg-surface-100-bg"
          >
            <img
              src={product.image_url}
              alt={product.title}
              className="h-32 w-full object-cover"
            />
            <div className="p-3">
              <p className="truncate text-sm text-surface-100-fg-default">{product.title}</p>
              <p className="mt-1 text-base font-medium text-text-accent">{formatPrice(product.price)}</p>
            </div>
          </div>
        ))}
      </div>
      {hasMore && (
        <div className="flex justify-center py-4">
          <button
            onClick={onLoadMore}
            disabled={loading}
            className="rounded-lg border border-input bg-surface-100-bg px-6 py-2 text-sm text-surface-100-fg-default hover:bg-muted/50 disabled:opacity-50"
          >
            {loading ? "加载中..." : "加载更多"}
          </button>
        </div>
      )}
    </div>
  );
}
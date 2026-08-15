import type { Product } from "@ec/sdk";

type Props = { items: Product[] };

export function formatPrice(cents: number): string {
  return `¥${(cents / 100).toFixed(2)}`;
}

export function HomeProductGrid({ items }: Props) {
  if (items.length === 0) return null;
  return (
    <div className="grid grid-cols-2 gap-3 sm:grid-cols-3 lg:grid-cols-4">
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
  );
}
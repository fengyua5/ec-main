import type { Product } from "@ec/sdk";
import { Slider } from "@ec/ui";
import { CmsTitle } from "./cms-title";
import { formatPrice } from "./cms-product-waterfall";

type Props = {
  title?: string;
  items: Product[];
};

export function CmsProductList({ title, items }: Props) {
  if (items.length === 0) return null;
  return (
    <div className="mb-3">
      {title && <CmsTitle title={title} />}
      <Slider
        items={items}
        options={{ slides: { spacing: 12, perView: 2.2 } }}
        className="overflow-hidden pt-3"
        slideClassName="first:ml-3 last:mr-3"
        renderSlide={(product) => (
          <div className="flex h-full flex-col overflow-hidden rounded-xl border bg-surface-100-bg">
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
        )}
      />
    </div>
  );
}
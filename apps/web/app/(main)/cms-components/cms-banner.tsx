import type { BannerItem } from "@ec/sdk";

type Props = { items: BannerItem[] };

export function CmsBanner({ items }: Props) {
  if (items.length === 0) return null;
  return (
    <div className="overflow-hidden rounded-2xl">
      {items.map((item, index) => {
        const inner = (
          <img
            src={item.image_url}
            alt={`banner-${index}`}
            className="h-48 w-full object-cover"
          />
        );
        return item.link_url ? (
          <a key={item.id} href={item.link_url}>
            {inner}
          </a>
        ) : (
          <div key={item.id}>{inner}</div>
        );
      })}
    </div>
  );
}
"use client";

import type { BannerItem } from "@ec/sdk";
import { Slider } from "@ec/ui";

type Props = { items: BannerItem[] };

export function CmsBanner({ items }: Props) {
  return (
    <Slider
      items={items}
      options={{ loop: true, slides: { perView: 1.15, spacing: 12 } }}
      showDots
      className="mt-3 overflow-hidden pb-3"
      slideClassName="first:ml-3 last:mr-3"
      renderSlide={(item) => {
        const img = (
          <img
            src={item.image_url}
            alt={item.description || "banner"}
            className="h-48 w-full object-cover rounded-2xl"
          />
        );
        return item.link_url ? (
          <a href={item.link_url}>{img}</a>
        ) : (
          img
        );
      }}
    />
  );
}
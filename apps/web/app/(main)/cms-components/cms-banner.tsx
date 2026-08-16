"use client";

import type { BannerItem } from "@ec/sdk";
import { Slider } from "@ec/ui";

type Props = { items: BannerItem[] };

export function CmsBanner({ items }: Props) {
  return (
    <Slider
      items={items}
      options={{ loop: true }}
      autoPlay
      showDots
      className="mx-3 mt-3 overflow-hidden rounded-2xl"
      renderSlide={(item) => {
        const img = (
          <img
            src={item.image_url}
            alt={item.description || "banner"}
            className="h-48 w-full object-cover"
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
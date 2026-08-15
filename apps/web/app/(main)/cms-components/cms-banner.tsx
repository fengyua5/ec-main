"use client";

import { useState, useEffect, useCallback } from "react";
import type { BannerItem } from "@ec/sdk";

type Props = { items: BannerItem[] };

export function CmsBanner({ items }: Props) {
  const [current, setCurrent] = useState(0);

  const goTo = useCallback((index: number) => {
    setCurrent(index);
  }, []);

  const goNext = useCallback(() => {
    setCurrent((prev) => (prev + 1) % items.length);
  }, [items.length]);

  useEffect(() => {
    if (items.length <= 1) return;
    const timer = setInterval(goNext, 4000);
    return () => clearInterval(timer);
  }, [goNext, items.length]);

  if (items.length === 0) return null;

  return (
    <div className="relative mx-3 mt-3 overflow-hidden rounded-2xl">
      <div
        className="flex transition-transform duration-500 ease-in-out"
        style={{ transform: `translateX(-${current * 100}%)` }}
      >
        {items.map((item, index) => {
          const inner = (
            <img
              src={item.image_url}
              alt={`banner-${index}`}
              className="h-48 w-full shrink-0 object-cover"
            />
          );
          return item.link_url ? (
            <a key={item.id} href={item.link_url} className="w-full shrink-0">
              {inner}
            </a>
          ) : (
            <div key={item.id} className="w-full shrink-0">
              {inner}
            </div>
          );
        })}
      </div>
      {items.length > 1 && (
        <div className="absolute bottom-2 left-1/2 flex -translate-x-1/2 gap-1.5">
          {items.map((_, index) => (
            <button
              key={index}
              onClick={() => goTo(index)}
              className={`size-2 rounded-full ${
                index === current ? "bg-white" : "bg-white/50"
              }`}
              aria-label={`banner-${index}`}
            />
          ))}
        </div>
      )}
    </div>
  );
}
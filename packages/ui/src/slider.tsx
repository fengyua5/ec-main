"use client";

import { useKeenSlider } from "keen-slider/react";
import "keen-slider/keen-slider.min.css";
import type { KeenSliderOptions } from "keen-slider";
import { useState, useCallback, useEffect, useRef } from "react";
import { clsx } from "clsx";

export type SliderProps<T> = {
  items: T[];
  renderSlide: (item: T, index: number) => React.ReactNode;
  options?: KeenSliderOptions;
  autoPlay?: boolean | { interval: number };
  showDots?: boolean;
  showArrows?: boolean;
  className?: string;
  slideClassName?: string;
};

export function Slider<T>({
  items,
  renderSlide,
  options = {},
  autoPlay,
  showDots = false,
  showArrows = false,
  className,
  slideClassName,
}: SliderProps<T>) {
  const interval = typeof autoPlay === "object" ? autoPlay.interval : 4000;
  const [current, setCurrent] = useState(0);
  const timerRef = useRef<ReturnType<typeof setInterval> | null>(null);

  const [sliderRef, instanceRef] = useKeenSlider<HTMLDivElement>({
    ...options,
    slideChanged(slider) {
      setCurrent(slider.track.details.rel);
      options.slideChanged?.(slider);
    },
  });

  const stopAutoPlay = useCallback(() => {
    if (timerRef.current) {
      clearInterval(timerRef.current);
      timerRef.current = null;
    }
  }, []);

  const startAutoPlay = useCallback(() => {
    stopAutoPlay();
    if (items.length <= 1) return;
    timerRef.current = setInterval(() => {
      instanceRef.current?.next();
    }, interval);
  }, [items.length, interval, instanceRef, stopAutoPlay]);

  useEffect(() => {
    if (!autoPlay) return;
    startAutoPlay();
    return stopAutoPlay;
  }, [autoPlay, startAutoPlay, stopAutoPlay]);

  if (items.length === 0) return null;

  return (
    <div className={clsx("relative", className)}>
      <div ref={sliderRef} className="keen-slider">
        {items.map((item, index) => (
          <div key={index} className={clsx("keen-slider__slide", slideClassName)}>
            {renderSlide(item, index)}
          </div>
        ))}
      </div>

      {showArrows && items.length > 1 && (
        <>
          <button
            onClick={() => instanceRef.current?.prev()}
            className="absolute left-2 top-1/2 z-10 flex size-8 -translate-y-1/2 items-center justify-center rounded-full bg-white/80 text-zinc-800 shadow hover:bg-white"
            aria-label="previous slide"
          >
            <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="m15 18-6-6 6-6"/></svg>
          </button>
          <button
            onClick={() => instanceRef.current?.next()}
            className="absolute right-2 top-1/2 z-10 flex size-8 -translate-y-1/2 items-center justify-center rounded-full bg-white/80 text-zinc-800 shadow hover:bg-white"
            aria-label="next slide"
          >
            <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="m9 18 6-6-6-6"/></svg>
          </button>
        </>
      )}

      {showDots && items.length > 1 && (
        <div className="absolute bottom-2 left-1/2 flex -translate-x-1/2 gap-1.5">
          {items.map((_, index) => (
            <button
              key={index}
              onClick={() => instanceRef.current?.moveToIdx(index)}
              className={clsx(
                "size-2 rounded-full transition-colors",
                index === current ? "bg-white" : "bg-white/50",
              )}
              aria-label={`slide-${index}`}
            />
          ))}
        </div>
      )}
    </div>
  );
}
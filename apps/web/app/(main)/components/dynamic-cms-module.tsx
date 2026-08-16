"use client";

import type { HomeModule, BannerItem, Product, Announcement } from "@ec/sdk";
import { Loader2 } from "lucide-react";
import { useCMS } from "../hooks/use-cms";
import { CmsBanner, CmsProductWaterfall, CmsProductList, CmsAnnouncement, CmsSearchBar } from "../cms-components";

type Props = { module: HomeModule };

export function DynamicCmsModule({ module }: Props) {
  const { data, loading, error } = useCMS(module);

  if (loading) {
    return (
      <div className="flex items-center justify-center py-8" data-testid="dynamic-cms-loading">
        <Loader2 className="size-5 animate-spin text-muted-foreground" />
      </div>
    );
  }

  if (error) {
    return <p className="text-sm text-red-600">{error}</p>;
  }

  switch (module.module_type) {
    case "banner":
      return <CmsBanner items={(data as { items: BannerItem[] } | null)?.items ?? []} />;
    case "product_recommend":
      return <CmsProductWaterfall title={module.title} items={(data as { items: Product[] } | null)?.items ?? []} />;
    case "product_list":
      return <CmsProductList title={module.title} items={(data as { items: Product[] } | null)?.items ?? []} />;
    case "announcement":
      return <CmsAnnouncement items={(data as { items: Announcement[] } | null)?.items ?? []} />;
    case "search_bar":
      return <CmsSearchBar />;
    default:
      return null;
  }
}
import type { ApiClient } from "./client";

export type ModuleType = "banner" | "product_recommend" | "announcement";

export type HomeModule = {
  id: number;
  module_type: ModuleType;
  title: string;
  data_source_url: string;
  sort_order: number;
};

export type HomeModulesResponse = {
  modules: HomeModule[];
};

export type BannerItem = {
  id: number;
  image_url: string;
  link_url: string;
};

export type BannerListResponse = {
  items: BannerItem[];
};

export type Announcement = {
  id: number;
  content: string;
};

export type AnnouncementListResponse = {
  items: Announcement[];
};

export type Product = {
  id: number;
  title: string;
  image_url: string;
  price: number;
};

export type ProductPublicListResponse = {
  items: Product[];
  total: number;
};

/** 首页可配置模块列表(仅启用) */
export function getHomeModules(client: ApiClient): Promise<HomeModulesResponse> {
  return client.request<HomeModulesResponse>("/api/v1/web/home/modules");
}

/** 首页 banner 列表 */
export function getHomeBanner(client: ApiClient): Promise<BannerListResponse> {
  return client.request<BannerListResponse>("/api/v1/web/home/banner");
}

/** 首页公告列表 */
export function getHomeAnnouncements(client: ApiClient): Promise<AnnouncementListResponse> {
  return client.request<AnnouncementListResponse>("/api/v1/web/home/announcement");
}

/** 首页推荐商品(公开) */
export function getPublicProducts(
  client: ApiClient,
  options?: { status?: string; page?: number; page_size?: number },
): Promise<ProductPublicListResponse> {
  const params = new URLSearchParams();
  if (options?.status) params.set("status", options.status);
  if (options?.page) params.set("page", String(options.page));
  if (options?.page_size) params.set("page_size", String(options.page_size));
  const query = params.toString();
  return client.request<ProductPublicListResponse>(
    `/api/v1/web/home/products${query ? `?${query}` : ""}`,
  );
}

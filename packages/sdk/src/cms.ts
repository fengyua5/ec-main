import type { ApiClient } from "./client";
import type { ModuleType } from "./home";

export type CmsModule = {
  id: number;
  module_type: ModuleType;
  title: string;
  data_source_url: string;
  sort_order: number;
  is_enabled: boolean;
  created_at: string;
  updated_at: string;
};

export type ModuleInput = {
  module_type: ModuleType;
  title: string;
  data_source_url: string;
  sort_order: number;
  is_enabled: boolean;
};

export type CmsProduct = {
  id: number;
  title: string;
  image_url: string;
  price: number;
  status: string;
  sort_order: number;
  created_at: string;
};

export type ProductInput = {
  title: string;
  image_url: string;
  price: number;
  status: string;
  sort_order: number;
};

export type CmsProductListResponse = {
  items: CmsProduct[];
  total: number;
  page: number;
  page_size: number;
};

export type CmsBanner = {
  id: number;
  image_url: string;
  link_url: string;
  sort_order: number;
  is_enabled: boolean;
  created_at: string;
};

export type BannerInput = {
  image_url: string;
  link_url: string;
  sort_order: number;
  is_enabled: boolean;
};

export type CmsBannerListResponse = {
  items: CmsBanner[];
};

export type CmsAnnouncement = {
  id: number;
  content: string;
  is_enabled: boolean;
  created_at: string;
};

export type AnnouncementInput = {
  content: string;
  is_enabled: boolean;
};

export type CmsAnnouncementListResponse = {
  items: CmsAnnouncement[];
};

export function getCmsModules(client: ApiClient): Promise<CmsModule[]> {
  return client.request<CmsModule[]>("/api/v1/admin/cms/modules");
}

export function createCmsModule(client: ApiClient, input: ModuleInput): Promise<CmsModule> {
  return client.request<CmsModule>("/api/v1/admin/cms/modules", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(input),
  });
}

export function updateCmsModule(
  client: ApiClient,
  moduleId: number,
  input: ModuleInput,
): Promise<CmsModule> {
  return client.request<CmsModule>(`/api/v1/admin/cms/modules/${moduleId}`, {
    method: "PATCH",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(input),
  });
}

export function deleteCmsModule(client: ApiClient, moduleId: number): Promise<void> {
  return client.request<void>(`/api/v1/admin/cms/modules/${moduleId}`, { method: "DELETE" });
}

export function moveCmsModule(
  client: ApiClient,
  moduleId: number,
  direction: "up" | "down",
): Promise<CmsModule[]> {
  return client.request<CmsModule[]>(`/api/v1/admin/cms/modules/${moduleId}/move`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ direction }),
  });
}

export function getCmsProducts(
  client: ApiClient,
  options?: { page?: number; page_size?: number; status?: string },
): Promise<CmsProductListResponse> {
  const params = new URLSearchParams();
  if (options?.page) params.set("page", String(options.page));
  if (options?.page_size) params.set("page_size", String(options.page_size));
  if (options?.status) params.set("status", options.status);
  const query = params.toString();
  return client.request<CmsProductListResponse>(`/api/v1/admin/cms/products${query ? `?${query}` : ""}`);
}

export function createCmsProduct(client: ApiClient, input: ProductInput): Promise<CmsProduct> {
  return client.request<CmsProduct>("/api/v1/admin/cms/products", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(input),
  });
}

export function updateCmsProduct(
  client: ApiClient,
  productId: number,
  input: ProductInput,
): Promise<CmsProduct> {
  return client.request<CmsProduct>(`/api/v1/admin/cms/products/${productId}`, {
    method: "PATCH",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(input),
  });
}

export function deleteCmsProduct(client: ApiClient, productId: number): Promise<void> {
  return client.request<void>(`/api/v1/admin/cms/products/${productId}`, { method: "DELETE" });
}

export function getCmsBanners(client: ApiClient): Promise<CmsBannerListResponse> {
  return client.request<CmsBannerListResponse>("/api/v1/admin/cms/banners");
}

export function createCmsBanner(client: ApiClient, input: BannerInput): Promise<CmsBanner> {
  return client.request<CmsBanner>("/api/v1/admin/cms/banners", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(input),
  });
}

export function updateCmsBanner(
  client: ApiClient,
  bannerId: number,
  input: BannerInput,
): Promise<CmsBanner> {
  return client.request<CmsBanner>(`/api/v1/admin/cms/banners/${bannerId}`, {
    method: "PATCH",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(input),
  });
}

export function deleteCmsBanner(client: ApiClient, bannerId: number): Promise<void> {
  return client.request<void>(`/api/v1/admin/cms/banners/${bannerId}`, { method: "DELETE" });
}

export function getCmsAnnouncements(client: ApiClient): Promise<CmsAnnouncementListResponse> {
  return client.request<CmsAnnouncementListResponse>("/api/v1/admin/cms/announcements");
}

export function createCmsAnnouncement(
  client: ApiClient,
  input: AnnouncementInput,
): Promise<CmsAnnouncement> {
  return client.request<CmsAnnouncement>("/api/v1/admin/cms/announcements", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(input),
  });
}

export function updateCmsAnnouncement(
  client: ApiClient,
  announcementId: number,
  input: AnnouncementInput,
): Promise<CmsAnnouncement> {
  return client.request<CmsAnnouncement>(`/api/v1/admin/cms/announcements/${announcementId}`, {
    method: "PATCH",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(input),
  });
}

export function deleteCmsAnnouncement(
  client: ApiClient,
  announcementId: number,
): Promise<void> {
  return client.request<void>(`/api/v1/admin/cms/announcements/${announcementId}`, {
    method: "DELETE",
  });
}

import { render, screen, cleanup } from "@testing-library/react";
import { afterEach, describe, it, expect, vi } from "vitest";
import { DynamicCmsModule } from "@/app/(main)/components/dynamic-cms-module";
import type { HomeModule } from "@ec/sdk";

afterEach(cleanup);

const dynamicBanner: HomeModule = {
  id: 1, module_type: "banner", title: "动态轮播", description: "",
  data_source_url: "/api/v1/web/home/banner", is_static: false, sort_order: 1,
};

describe("DynamicCmsModule", () => {
  it("shows loading spinner initially", () => {
    render(<DynamicCmsModule module={dynamicBanner} />);
    expect(screen.getByTestId("dynamic-cms-loading")).toBeInTheDocument();
  });

  it("renders banner after data loads", async () => {
    const mockData = { items: [{ id: 1, image_url: "https://example.com/b.jpg", description: "", link_url: "" }] };
    vi.spyOn(globalThis, "fetch").mockResolvedValue({
      ok: true,
      json: () => Promise.resolve(mockData),
    } as Response);

    render(<DynamicCmsModule module={dynamicBanner} />);

    await screen.findByAltText("banner");
    expect(screen.getByAltText("banner")).toBeInTheDocument();

    vi.restoreAllMocks();
  });

  it("shows error on fetch failure", async () => {
    vi.spyOn(globalThis, "fetch").mockRejectedValue(new Error("fail"));

    render(<DynamicCmsModule module={dynamicBanner} />);

    await screen.findByText("数据加载失败");
    expect(screen.getByText("数据加载失败")).toBeInTheDocument();

    vi.restoreAllMocks();
  });
});
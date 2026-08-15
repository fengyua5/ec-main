import { render, screen, cleanup } from "@testing-library/react";
import { afterEach, describe, it, expect } from "vitest";
import { HomeModuleRenderer, type ModulePayloads } from "@/app/(main)/components/home-module-renderer";
import type { HomeModule } from "@ec/sdk";

afterEach(cleanup);

const staticData: Partial<ModulePayloads> = {
  banner: [{ id: 1, image_url: "https://example.com/banner.jpg", description: "", link_url: "/p" }],
  product_recommend: [{ id: 1, title: "商品1", image_url: "", price: 9900 }],
  announcement: [{ id: 1, content: "公告1" }],
};

describe("HomeModuleRenderer", () => {
  it("renders static banner module", () => {
    const modules: HomeModule[] = [
      { id: 1, module_type: "banner", title: "轮播", description: "", data_source_url: "/api/v1/web/home/banner", is_static: true, sort_order: 1 },
    ];
    render(<HomeModuleRenderer modules={modules} staticData={staticData} />);
    expect(screen.getByAltText("banner-0")).toBeInTheDocument();
  });

  it("renders static product grid module", () => {
    const modules: HomeModule[] = [
      { id: 2, module_type: "product_recommend", title: "商品推荐", description: "", data_source_url: "/api/v1/web/home/products", is_static: true, sort_order: 1 },
    ];
    render(<HomeModuleRenderer modules={modules} staticData={staticData} />);
    expect(screen.getByText("商品1")).toBeInTheDocument();
  });

  it("renders static announcement module", () => {
    const modules: HomeModule[] = [
      { id: 3, module_type: "announcement", title: "公告", description: "", data_source_url: "/api/v1/web/home/announcement", is_static: true, sort_order: 1 },
    ];
    render(<HomeModuleRenderer modules={modules} staticData={staticData} />);
    expect(screen.getByText("公告1")).toBeInTheDocument();
  });

  it("renders search bar module (static, no data_source_url)", () => {
    const modules: HomeModule[] = [
      { id: 5, module_type: "search_bar", title: "搜索", description: "", data_source_url: "", is_static: true, sort_order: 0 },
    ];
    render(<HomeModuleRenderer modules={modules} staticData={{}} />);
    expect(screen.getByPlaceholderText("搜索商品…")).toBeInTheDocument();
  });

  it("renders dynamic module wrapper for non-static module", () => {
    const modules: HomeModule[] = [
      { id: 6, module_type: "banner", title: "动态轮播", description: "", data_source_url: "/api/v1/web/home/banner", is_static: false, sort_order: 1 },
    ];
    render(<HomeModuleRenderer modules={modules} staticData={{}} />);
    expect(screen.getByTestId("dynamic-cms-loading")).toBeInTheDocument();
  });

  it("renders nothing for unknown module type", () => {
    const unknownModule = {
      id: 4,
      module_type: "unknown",
      title: "未知模块",
      description: "",
      data_source_url: "",
      is_static: false,
      sort_order: 4,
    } as unknown as HomeModule;
    const { container } = render(<HomeModuleRenderer modules={[unknownModule]} staticData={{}} />);
    expect(container.querySelectorAll("*").length).toBe(1);
  });
});
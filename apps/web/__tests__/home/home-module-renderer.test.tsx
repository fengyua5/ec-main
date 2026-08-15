import { render, screen, cleanup } from "@testing-library/react";
import { afterEach, describe, it, expect } from "vitest";
import { HomeModuleRenderer, type ModulePayloads } from "@/app/(main)/components/home-module-renderer";
import type { HomeModule } from "@ec/sdk";

afterEach(cleanup);

const data: ModulePayloads = {
  banner: [{ id: 1, image_url: "https://example.com/banner.jpg", link_url: "/p" }],
  product_recommend: [{ id: 1, title: "商品1", image_url: "", price: 9900 }],
  announcement: [{ id: 1, content: "公告1" }],
};

describe("HomeModuleRenderer", () => {
  it("renders banner module", () => {
    const modules: HomeModule[] = [
      { id: 1, module_type: "banner", title: "轮播", data_source_url: "", sort_order: 1 },
    ];
    render(<HomeModuleRenderer modules={modules} data={data} />);
    expect(screen.getByAltText("banner-0")).toBeInTheDocument();
  });

  it("renders product grid module", () => {
    const modules: HomeModule[] = [
      { id: 2, module_type: "product_recommend", title: "商品推荐", data_source_url: "", sort_order: 1 },
    ];
    render(<HomeModuleRenderer modules={modules} data={data} />);
    expect(screen.getByText("商品1")).toBeInTheDocument();
  });

  it("renders announcement module", () => {
    const modules: HomeModule[] = [
      { id: 3, module_type: "announcement", title: "公告", data_source_url: "", sort_order: 1 },
    ];
    render(<HomeModuleRenderer modules={modules} data={data} />);
    expect(screen.getByText("公告1")).toBeInTheDocument();
  });

  it("renders nothing for unknown module type", () => {
    const unknownModule = {
      id: 4,
      module_type: "unknown",
      title: "未知模块",
      data_source_url: "",
      sort_order: 4,
    } as unknown as HomeModule;
    const { container } = render(<HomeModuleRenderer modules={[unknownModule]} data={data} />);
    expect(container.querySelectorAll("*").length).toBe(1);
  });
});
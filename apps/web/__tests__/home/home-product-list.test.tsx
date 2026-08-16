import { render, screen, cleanup } from "@testing-library/react";
import { afterEach, describe, it, expect } from "vitest";
import { CmsProductList } from "@/app/(main)/cms-components/cms-product-list";

afterEach(cleanup);

describe("CmsProductList", () => {
  it("renders nothing when empty", () => {
    const { container } = render(<CmsProductList items={[]} />);
    expect(container.innerHTML).toBe("");
  });

  it("renders product titles and prices", () => {
    render(
      <CmsProductList
        items={[
          { id: 1, title: "商品1", image_url: "", price: 9900 },
          { id: 2, title: "商品2", image_url: "", price: 12900 },
        ]}
      />,
    );
    expect(screen.getByText("商品1")).toBeInTheDocument();
    expect(screen.getByText("¥99.00")).toBeInTheDocument();
    expect(screen.getByText("商品2")).toBeInTheDocument();
    expect(screen.getByText("¥129.00")).toBeInTheDocument();
  });

  it("renders title when provided", () => {
    render(
      <CmsProductList
        title="推荐商品"
        items={[
          { id: 1, title: "商品1", image_url: "", price: 9900 },
        ]}
      />,
    );
    expect(screen.getByText("推荐商品")).toBeInTheDocument();
  });

  it("uses slider without native scrollbar", () => {
    render(
      <CmsProductList
        items={[
          { id: 1, title: "商品1", image_url: "", price: 9900 },
          { id: 2, title: "商品2", image_url: "", price: 12900 },
          { id: 3, title: "商品3", image_url: "", price: 19900 },
        ]}
      />,
    );
    expect(screen.getByText("商品1").closest(".keen-slider")).toBeTruthy();
    expect(document.querySelector(".overflow-x-auto")).toBeNull();
  });
});
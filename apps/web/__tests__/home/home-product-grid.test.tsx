import { render, screen, cleanup } from "@testing-library/react";
import { afterEach, describe, it, expect } from "vitest";
import { HomeProductGrid, formatPrice } from "@/app/(main)/components/home-product-grid";

afterEach(cleanup);

describe("formatPrice", () => {
  it("formats cents into yuan with two decimals", () => {
    expect(formatPrice(9900)).toBe("¥99.00");
    expect(formatPrice(12900)).toBe("¥129.00");
  });
});

describe("HomeProductGrid", () => {
  it("renders nothing when empty", () => {
    const { container } = render(<HomeProductGrid items={[]} />);
    expect(container.innerHTML).toBe("");
  });

  it("renders product titles and prices", () => {
    render(
      <HomeProductGrid
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
});
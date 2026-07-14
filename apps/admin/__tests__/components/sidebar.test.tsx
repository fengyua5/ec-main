import { describe, it, expect, afterEach } from "vitest";
import { render, screen, cleanup } from "@testing-library/react";
import { Sidebar } from "../../app/components/sidebar";

afterEach(cleanup);

describe("Sidebar", () => {
  it("renders nav items", () => {
    render(<Sidebar />);
    expect(screen.getByText("概览")).toBeDefined();
    expect(screen.getByText("订单管理")).toBeDefined();
    expect(screen.getByText("商品管理")).toBeDefined();
    expect(screen.getByText("用户管理")).toBeDefined();
  });

  it("renders version text", () => {
    render(<Sidebar />);
    expect(screen.getAllByText("EC Main Admin v0.1")).toHaveLength(1);
  });

  it("概览 links to /", () => {
    render(<Sidebar />);
    const link = screen.getByText("概览").closest("a");
    expect(link?.getAttribute("href")).toBe("/");
  });
});

import { describe, it, expect, vi, afterEach } from "vitest";
import { render, screen, cleanup } from "@testing-library/react";
import { Sidebar } from "../../app/components/sidebar";

vi.mock("next/navigation", () => ({
  usePathname: vi.fn(),
}));

import { usePathname } from "next/navigation";

const mockUsePathname = vi.mocked(usePathname);

afterEach(() => {
  cleanup();
  vi.restoreAllMocks();
});

function activeLinks() {
  return screen
    .getAllByText(/概览|FAQ 管理|客服消息|订单管理|商品管理|用户管理/)
    .map((el) => el.closest("a"))
    .filter((link): link is HTMLAnchorElement => link?.getAttribute("aria-current") === "page");
}

describe("Sidebar", () => {
  it("renders nav items", () => {
    mockUsePathname.mockReturnValue("/");
    render(<Sidebar />);
    expect(screen.getByText("概览")).toBeDefined();
    expect(screen.getByText("订单管理")).toBeDefined();
    expect(screen.getByText("商品管理")).toBeDefined();
    expect(screen.getByText("用户管理")).toBeDefined();
  });

  it("renders version text", () => {
    mockUsePathname.mockReturnValue("/");
    render(<Sidebar />);
    expect(screen.getAllByText("EC Main Admin v0.1")).toHaveLength(1);
  });

  it("概览 links to /", () => {
    mockUsePathname.mockReturnValue("/");
    render(<Sidebar />);
    const link = screen.getByText("概览").closest("a");
    expect(link?.getAttribute("href")).toBe("/");
  });

  it("highlights 概览 as active on /", () => {
    mockUsePathname.mockReturnValue("/");
    render(<Sidebar />);
    expect(screen.getByText("概览").closest("a")).toHaveAttribute("aria-current", "page");
  });

  it("does not highlight 概览 on other routes", () => {
    mockUsePathname.mockReturnValue("/faq");
    render(<Sidebar />);
    expect(screen.getByText("概览").closest("a")).not.toHaveAttribute("aria-current");
  });

  it("highlights FAQ 管理 as active on /faq", () => {
    mockUsePathname.mockReturnValue("/faq");
    render(<Sidebar />);
    expect(screen.getByText("FAQ 管理").closest("a")).toHaveAttribute("aria-current", "page");
  });

  it("highlights 订单管理 as active on nested order page", () => {
    mockUsePathname.mockReturnValue("/orders/12345");
    render(<Sidebar />);
    expect(screen.getByText("订单管理").closest("a")).toHaveAttribute("aria-current", "page");
  });

  it("highlights exactly one nav item as active", () => {
    mockUsePathname.mockReturnValue("/orders");
    render(<Sidebar />);
    expect(activeLinks()).toHaveLength(1);
    expect(activeLinks()[0]).toHaveTextContent("订单管理");
  });
});

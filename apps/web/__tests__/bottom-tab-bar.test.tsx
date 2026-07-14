import { render, screen, cleanup } from "@testing-library/react";
import { afterEach, describe, it, expect, vi } from "vitest";

afterEach(cleanup);

const mockUsePathname = vi.fn().mockReturnValue("/");

vi.mock("next/navigation", () => ({
  usePathname: () => mockUsePathname(),
  useRouter: () => ({ push: vi.fn() }),
}));

import { BottomTabBar } from "@/app/components/bottom-tab-bar";

describe("BottomTabBar", () => {
  it("renders three tabs: 首页, AI 客服, 账号", () => {
    render(<BottomTabBar />);
    expect(screen.getByText("首页")).toBeInTheDocument();
    expect(screen.getByText("AI 客服")).toBeInTheDocument();
    expect(screen.getByText("账号")).toBeInTheDocument();
  });

  it("highlights the active tab based on current path", () => {
    mockUsePathname.mockReturnValue("/ai");
    render(<BottomTabBar />);
    const aiTab = screen.getByText("AI 客服").closest("a");
    expect(aiTab).toHaveClass("text-primary");
  });

  it("links tabs to correct routes", () => {
    mockUsePathname.mockReturnValue("/");
    render(<BottomTabBar />);
    const homeLink = screen.getByText("首页").closest("a");
    expect(homeLink).toHaveAttribute("href", "/");

    const aiLink = screen.getByText("AI 客服").closest("a");
    expect(aiLink).toHaveAttribute("href", "/ai");

    const accountLink = screen.getByText("账号").closest("a");
    expect(accountLink).toHaveAttribute("href", "/account");
  });
});

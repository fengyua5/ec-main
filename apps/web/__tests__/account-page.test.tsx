import { render, screen, cleanup, waitFor } from "@testing-library/react";
import { afterEach, describe, it, expect, vi } from "vitest";

const mockPush = vi.fn();
const mockGetMe = vi.fn();

vi.mock("next/navigation", () => ({
  useRouter: () => ({ push: mockPush }),
}));

vi.mock("@ec/sdk", () => ({
  createApiClient: vi.fn(),
  getMe: () => mockGetMe(),
  logout: vi.fn(),
}));

afterEach(() => {
  cleanup();
  vi.clearAllMocks();
});

import AccountPage from "@/app/(main)/account/page";

describe("AccountPage", () => {
  it("shows login prompt when user is not authenticated", async () => {
    mockGetMe.mockRejectedValue(new Error("not logged in"));
    render(<AccountPage />);
    expect(await screen.findByText("未登录")).toBeInTheDocument();
    expect(screen.getByText("请登录后查看账号信息")).toBeInTheDocument();
    expect(screen.getByRole("link", { name: "登录" })).toHaveAttribute("href", "/login");
    expect(screen.getByRole("link", { name: "注册" })).toHaveAttribute("href", "/register");
  });

  it("shows user info when authenticated", async () => {
    mockGetMe.mockResolvedValue({
      id: 1,
      username: "testuser",
      email: "test@example.com",
      role: "buyer",
      created_at: "2026-01-01T00:00:00Z",
    });
    render(<AccountPage />);
    await waitFor(() => {
      expect(screen.getByText("testuser")).toBeInTheDocument();
    });
    expect(screen.getByText("test@example.com")).toBeInTheDocument();
    expect(screen.getByText("buyer")).toBeInTheDocument();
  });

  it("shows loading state initially", () => {
    mockGetMe.mockReturnValue(new Promise(() => {}));
    render(<AccountPage />);
    expect(screen.getByText("加载中...")).toBeInTheDocument();
  });
});

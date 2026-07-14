import { describe, it, expect, vi, afterEach } from "vitest";
import { render, screen, waitFor, cleanup } from "@testing-library/react";
import { AdminAuthHeader } from "../../app/components/auth-header";

afterEach(() => {
  cleanup();
  vi.restoreAllMocks();
});

const mockUser = {
  id: 1,
  username: "admin01",
  email: "admin@example.com",
  role: "admin",
};

describe("AdminAuthHeader", () => {
  it("shows login/register links when not authenticated", async () => {
    vi.spyOn(globalThis, "fetch").mockRejectedValue(new Error("unauthorized"));

    render(<AdminAuthHeader />);

    await waitFor(() => {
      expect(screen.getByText("登录")).toBeDefined();
      expect(screen.getByText("注册")).toBeDefined();
    });
  });

  it("shows username and logout when authenticated", async () => {
    vi.spyOn(globalThis, "fetch").mockResolvedValue(
      new Response(JSON.stringify(mockUser), { status: 200 }),
    );

    render(<AdminAuthHeader />);

    await waitFor(() => {
      expect(screen.getByText("admin01")).toBeDefined();
    });
  });

  it("shows email when username is null", async () => {
    vi.spyOn(globalThis, "fetch").mockResolvedValue(
      new Response(JSON.stringify({ ...mockUser, username: null }), { status: 200 }),
    );

    render(<AdminAuthHeader />);

    await waitFor(() => {
      expect(screen.getByText("admin@example.com")).toBeDefined();
    });
  });
});

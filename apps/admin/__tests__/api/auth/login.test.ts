import { describe, it, expect, vi, beforeEach } from "vitest";

const mockBackendResponse = {
  user: { id: 1, email: "admin@example.com", role: "admin" },
};

const mockSetCookie = "token=eyJhbGci; HttpOnly; SameSite=Lax; Max-Age=86400; Path=/";

describe("POST /api/auth/login", () => {
  beforeEach(() => {
    vi.restoreAllMocks();
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    (globalThis as any).Headers = class MockHeaders {
      _headers: Record<string, string> = {};
      append(k: string, v: string) { this._headers[k] = v; }
      get(k: string) { return this._headers[k]; }
    };
  });

  it("proxies login request to backend and forwards Set-Cookie", async () => {
    vi.spyOn(globalThis, "fetch").mockResolvedValue(
      new Response(JSON.stringify(mockBackendResponse), {
        status: 200,
        headers: { "Content-Type": "application/json", "Set-Cookie": mockSetCookie },
      }),
    );

    const { POST } = await import("../../../app/api/auth/login/route");

    const request = new Request("http://localhost:3001/api/auth/login", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ email: "admin@example.com", password: "admin123" }),
    });

    const response = await POST(request);
    const data = await response.json();

    expect(response.status).toBe(200);
    expect(data.user.email).toBe("admin@example.com");
    expect(globalThis.fetch).toHaveBeenCalledWith(
      "http://localhost:8000/api/v1/admin/auth/login",
      expect.objectContaining({
        method: "POST",
        body: JSON.stringify({ email: "admin@example.com", password: "admin123" }),
      }),
    );
  });

  it("forwards error response from backend", async () => {
    vi.spyOn(globalThis, "fetch").mockResolvedValue(
      new Response(JSON.stringify({ detail: "邮箱或密码不正确" }), {
        status: 401,
        headers: { "Content-Type": "application/json" },
      }),
    );

    const { POST } = await import("../../../app/api/auth/login/route");

    const request = new Request("http://localhost:3001/api/auth/login", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ email: "wrong@example.com", password: "wrong" }),
    });

    const response = await POST(request);
    const data = await response.json();

    expect(response.status).toBe(401);
    expect(data.detail).toBe("邮箱或密码不正确");
  });
});

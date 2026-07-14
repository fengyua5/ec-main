import { describe, it, expect, vi, beforeEach } from "vitest";
import { NextResponse } from "next/server";
import type { NextRequest } from "next/server";

function mockRequest(pathname: string, token?: string): NextRequest {
  const url = new URL(`http://localhost:3001${pathname}`);
  return {
    nextUrl: Object.assign(url, {
      clone: () => new URL(url.toString()),
    }),
    cookies: {
      get: vi.fn(() => (token ? { name: "token", value: token } : undefined)),
    },
  } as unknown as NextRequest;
}

const { proxy } = await import("../proxy");

describe("proxy", () => {
  beforeEach(() => {
    vi.restoreAllMocks();
  });

  it("allows /login without token", () => {
    const req = mockRequest("/login");
    const res = proxy(req);
    expect(res).toBeInstanceOf(NextResponse);
    expect((res as NextResponse).status).toBe(200);
  });

  it("allows /register without token", () => {
    const req = mockRequest("/register");
    const res = proxy(req);
    expect(res).toBeInstanceOf(NextResponse);
    expect((res as NextResponse).status).toBe(200);
  });

  it("allows /api/* without token", () => {
    const req = mockRequest("/api/auth/login");
    const res = proxy(req);
    expect(res).toBeInstanceOf(NextResponse);
    expect((res as NextResponse).status).toBe(200);
  });

  it("allows /_next/* without token", () => {
    const req = mockRequest("/_next/static/chunk.js");
    const res = proxy(req);
    expect(res).toBeInstanceOf(NextResponse);
    expect((res as NextResponse).status).toBe(200);
  });

  it("redirects to /login when accessing / without token", () => {
    const req = mockRequest("/");
    const res = proxy(req);
    expect(res).toBeInstanceOf(NextResponse);
    expect((res as NextResponse).headers.get("location")).toBe("http://localhost:3001/login");
  });

  it("allows / when token is present", () => {
    const req = mockRequest("/", "valid-jwt-token");
    const res = proxy(req);
    expect(res).toBeInstanceOf(NextResponse);
    expect((res as NextResponse).status).toBe(200);
  });

  it("redirects to /login when accessing /orders without token", () => {
    const req = mockRequest("/orders");
    const res = proxy(req);
    expect(res).toBeInstanceOf(NextResponse);
    expect((res as NextResponse).headers.get("location")).toBe("http://localhost:3001/login");
  });

  it("allows /orders when token is present", () => {
    const req = mockRequest("/orders", "valid-jwt-token");
    const res = proxy(req);
    expect(res).toBeInstanceOf(NextResponse);
    expect((res as NextResponse).status).toBe(200);
  });
});

import { renderHook, waitFor, cleanup } from "@testing-library/react";
import { afterEach, describe, it, expect, vi } from "vitest";
import { useCMS } from "@/app/(main)/hooks/use-cms";

afterEach(cleanup);

const staticModule = { is_static: true, data_source_url: "" };
const staticModuleWithUrl = { is_static: true, data_source_url: "/api/v1/web/home/banner" };
const dynamicModule = { is_static: false, data_source_url: "/api/v1/web/home/banner" };
const dynamicModuleNoUrl = { is_static: false, data_source_url: "" };

describe("useCMS", () => {
  it("returns null data immediately for static module without data_source_url", () => {
    const { result } = renderHook(() => useCMS(staticModule));
    expect(result.current.data).toBeNull();
    expect(result.current.loading).toBe(false);
    expect(result.current.error).toBeNull();
  });

  it("returns initialData for static module with data_source_url", () => {
    const initialData = { items: [{ id: 1, image_url: "", description: "", link_url: "" }] };
    const { result } = renderHook(() => useCMS(staticModuleWithUrl, initialData));
    expect(result.current.data).toEqual(initialData);
    expect(result.current.loading).toBe(false);
  });

  it("fetches data for dynamic module", async () => {
    const mockData = { items: [{ id: 1, image_url: "", description: "", link_url: "" }] };
    const fetchSpy = vi.spyOn(globalThis, "fetch").mockResolvedValue({
      ok: true,
      json: () => Promise.resolve(mockData),
    } as Response);

    const { result } = renderHook(() => useCMS(dynamicModule));

    expect(result.current.loading).toBe(true);

    await waitFor(() => {
      expect(result.current.data).toEqual(mockData);
    });

    expect(result.current.loading).toBe(false);
    expect(result.current.error).toBeNull();
    fetchSpy.mockRestore();
  });

  it("does not fetch for dynamic module without data_source_url", () => {
    const fetchSpy = vi.spyOn(globalThis, "fetch");
    const { result } = renderHook(() => useCMS(dynamicModuleNoUrl));
    expect(result.current.data).toBeNull();
    expect(result.current.loading).toBe(false);
    expect(result.current.error).toBeNull();
    expect(fetchSpy).not.toHaveBeenCalled();
    fetchSpy.mockRestore();
  });

  it("sets error on fetch failure for dynamic module", async () => {
    const fetchSpy = vi.spyOn(globalThis, "fetch").mockRejectedValue(new Error("Network error"));

    const { result } = renderHook(() => useCMS(dynamicModule));

    await waitFor(() => {
      expect(result.current.error).toBe("数据加载失败");
    });

    expect(result.current.data).toBeNull();
    expect(result.current.loading).toBe(false);
    fetchSpy.mockRestore();
  });
});
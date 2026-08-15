"use client";

import { useEffect, useState, useCallback } from "react";
import { Loader2, Pencil, Trash2 } from "lucide-react";
import { createApiClient } from "@ec/sdk/client";
import { getCmsBanners, createCmsBanner, updateCmsBanner, deleteCmsBanner } from "@ec/sdk";
import type { CmsBanner, BannerInput } from "@ec/sdk";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";

const client = createApiClient({
  baseUrl: process.env.NEXT_PUBLIC_API_URL || "",
});

const emptyForm: BannerInput = { image_url: "", description: "", link_url: "", sort_order: 0, is_enabled: true };

export default function CmsBannersPage() {
  const [items, setItems] = useState<CmsBanner[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [form, setForm] = useState<BannerInput>({ ...emptyForm });
  const [editingId, setEditingId] = useState<number | null>(null);

  const loadBanners = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      setItems((await getCmsBanners(client)).items);
    } catch {
      setError("加载 Banner 失败");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    loadBanners();
  }, [loadBanners]);

  function resetForm() {
    setForm({ ...emptyForm });
    setEditingId(null);
  }

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError(null);
    try {
      if (editingId === null) {
        await createCmsBanner(client, { ...form, sort_order: Number(form.sort_order) || 0 });
      } else {
        await updateCmsBanner(client, editingId, { ...form, sort_order: Number(form.sort_order) || 0 });
      }
      resetForm();
      await loadBanners();
    } catch {
      setError("保存 Banner 失败");
    }
  }

  async function handleDelete(id: number) {
    if (!confirm("确认删除?")) return;
    try {
      await deleteCmsBanner(client, id);
      await loadBanners();
    } catch {
      setError("删除 Banner 失败");
    }
  }

  function handleEdit(item: CmsBanner) {
    setEditingId(item.id);
    setForm({ image_url: item.image_url, description: item.description, link_url: item.link_url, sort_order: item.sort_order, is_enabled: item.is_enabled });
  }

  return (
    <section className="space-y-6">
      <h1 className="text-2xl font-semibold">Banner 管理</h1>
      {error && <p className="text-sm text-red-600">{error}</p>}

      <form onSubmit={handleSubmit} className="space-y-3 rounded-lg border p-4">
        <div className="flex flex-wrap items-end gap-3">
          <div className="min-w-64 flex-1">
            <label className="mb-1 block text-xs text-muted-foreground">图片 URL</label>
            <Input value={form.image_url} onChange={(e) => setForm({ ...form, image_url: e.target.value })} placeholder="https://..." />
          </div>
          <div className="min-w-48 flex-1">
            <label className="mb-1 block text-xs text-muted-foreground">描述</label>
            <Input value={form.description} onChange={(e) => setForm({ ...form, description: e.target.value })} placeholder="Banner 描述" />
          </div>
          <div className="min-w-48 flex-1">
            <label className="mb-1 block text-xs text-muted-foreground">跳转链接</label>
            <Input value={form.link_url} onChange={(e) => setForm({ ...form, link_url: e.target.value })} />
          </div>
          <div>
            <label className="mb-1 block text-xs text-muted-foreground">排序</label>
            <Input type="number" value={form.sort_order} onChange={(e) => setForm({ ...form, sort_order: Number(e.target.value) })} className="w-24" />
          </div>
          <label className="flex items-center gap-2 pb-1 text-sm">
            <input type="checkbox" checked={form.is_enabled} onChange={(e) => setForm({ ...form, is_enabled: e.target.checked })} />
            启用
          </label>
          <Button type="submit">{editingId === null ? "新增" : "更新"}</Button>
          {editingId !== null && (
            <Button type="button" variant="outline" onClick={resetForm}>取消</Button>
          )}
        </div>
      </form>

      {loading ? (
        <div className="flex items-center justify-center py-12">
          <Loader2 className="size-6 animate-spin text-muted-foreground" />
        </div>
      ) : items.length === 0 ? (
        <p className="py-8 text-center text-sm text-muted-foreground">暂无 Banner</p>
      ) : (
        <div className="grid grid-cols-2 gap-4 md:grid-cols-3">
          {items.map((item) => (
            <div key={item.id} className="overflow-hidden rounded-lg border">
              {/* eslint-disable-next-line @next/next/no-img-element */}
              <img src={item.image_url} alt={item.link_url} className="h-32 w-full object-cover" />
              <div className="flex items-center justify-between p-3">
                <div className="min-w-0 flex-1">
                  <p className="truncate text-sm font-medium">{item.description || "无描述"}</p>
                  <span className="block truncate text-xs text-muted-foreground">{item.link_url || "无链接"}</span>
                </div>
                <div className="flex gap-2 ml-2">
                  <button onClick={() => handleEdit(item)} className="text-blue-600 hover:underline" aria-label="编辑">
                    <Pencil className="size-4" />
                  </button>
                  <button onClick={() => handleDelete(item.id)} className="text-red-600 hover:underline" aria-label="删除">
                    <Trash2 className="size-4" />
                  </button>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}
    </section>
  );
}
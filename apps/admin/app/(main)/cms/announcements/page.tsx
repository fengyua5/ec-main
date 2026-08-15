"use client";

import { useEffect, useState, useCallback } from "react";
import { Loader2, Pencil, Trash2 } from "lucide-react";
import { createApiClient } from "@ec/sdk/client";
import { getCmsAnnouncements, createCmsAnnouncement, updateCmsAnnouncement, deleteCmsAnnouncement } from "@ec/sdk";
import type { CmsAnnouncement, AnnouncementInput } from "@ec/sdk";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";

const client = createApiClient({
  baseUrl: process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000",
});

const emptyForm: AnnouncementInput = { content: "", is_enabled: true };

export default function CmsAnnouncementsPage() {
  const [items, setItems] = useState<CmsAnnouncement[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [form, setForm] = useState<AnnouncementInput>({ ...emptyForm });
  const [editingId, setEditingId] = useState<number | null>(null);

  const loadAnnouncements = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      setItems((await getCmsAnnouncements(client)).items);
    } catch {
      setError("加载公告失败");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    loadAnnouncements();
  }, [loadAnnouncements]);

  function resetForm() {
    setForm({ ...emptyForm });
    setEditingId(null);
  }

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError(null);
    try {
      if (editingId === null) {
        await createCmsAnnouncement(client, form);
      } else {
        await updateCmsAnnouncement(client, editingId, form);
      }
      resetForm();
      await loadAnnouncements();
    } catch {
      setError("保存公告失败");
    }
  }

  async function handleDelete(id: number) {
    if (!confirm("确认删除?")) return;
    try {
      await deleteCmsAnnouncement(client, id);
      await loadAnnouncements();
    } catch {
      setError("删除公告失败");
    }
  }

  function handleEdit(item: CmsAnnouncement) {
    setEditingId(item.id);
    setForm({ content: item.content, is_enabled: item.is_enabled });
  }

  return (
    <section className="space-y-6">
      <h1 className="text-2xl font-semibold">公告管理</h1>
      {error && <p className="text-sm text-red-600">{error}</p>}

      <form onSubmit={handleSubmit} className="flex flex-wrap items-end gap-3 rounded-lg border p-4">
        <div className="min-w-72 flex-1">
          <label className="mb-1 block text-xs text-muted-foreground">公告内容</label>
          <Input value={form.content} onChange={(e) => setForm({ ...form, content: e.target.value })} placeholder="公告内容" />
        </div>
        <label className="flex items-center gap-2 pb-1 text-sm">
          <input type="checkbox" checked={form.is_enabled} onChange={(e) => setForm({ ...form, is_enabled: e.target.checked })} />
          启用
        </label>
        <Button type="submit">{editingId === null ? "新增" : "更新"}</Button>
        {editingId !== null && (
          <Button type="button" variant="outline" onClick={resetForm}>取消</Button>
        )}
      </form>

      {loading ? (
        <div className="flex items-center justify-center py-12">
          <Loader2 className="size-6 animate-spin text-muted-foreground" />
        </div>
      ) : items.length === 0 ? (
        <p className="py-8 text-center text-sm text-muted-foreground">暂无公告</p>
      ) : (
        <ul className="space-y-2">
          {items.map((item) => (
            <li key={item.id} className="flex items-center justify-between rounded-lg border px-4 py-3">
              <div className="flex items-center gap-3">
                <span className="text-sm">{item.content}</span>
                {item.is_enabled ? (
                  <span className="inline-block rounded-full bg-green-100 px-2 py-0.5 text-xs text-green-700">启用</span>
                ) : (
                  <span className="inline-block rounded-full bg-gray-100 px-2 py-0.5 text-xs text-gray-600">停用</span>
                )}
              </div>
              <div className="flex gap-2">
                <button onClick={() => handleEdit(item)} className="text-blue-600 hover:underline" aria-label="编辑">
                  <Pencil className="size-4" />
                </button>
                <button onClick={() => handleDelete(item.id)} className="text-red-600 hover:underline" aria-label="删除">
                  <Trash2 className="size-4" />
                </button>
              </div>
            </li>
          ))}
        </ul>
      )}
    </section>
  );
}
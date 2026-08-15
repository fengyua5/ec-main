"use client";

import { useEffect, useState, useCallback } from "react";
import { Loader2, Pencil, Trash2 } from "lucide-react";
import { createApiClient } from "@ec/sdk/client";
import { getCmsProducts, createCmsProduct, updateCmsProduct, deleteCmsProduct } from "@ec/sdk";
import type { CmsProduct, ProductInput } from "@ec/sdk";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";

const client = createApiClient({
  baseUrl: process.env.NEXT_PUBLIC_API_URL || "",
});

const PAGE_SIZE = 20;

const emptyForm: ProductInput = {
  title: "",
  image_url: "",
  price: 0,
  status: "active",
  sort_order: 0,
};

const selectClassName =
  "h-8 rounded-lg border border-input bg-transparent px-2.5 text-sm outline-none focus-visible:border-ring focus-visible:ring-3 focus-visible:ring-ring/50";

export default function CmsProductsPage() {
  const [items, setItems] = useState<CmsProduct[]>([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [form, setForm] = useState<ProductInput>({ ...emptyForm });
  const [editingId, setEditingId] = useState<number | null>(null);

  const loadProducts = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await getCmsProducts(client, { page, page_size: PAGE_SIZE });
      setItems(res.items);
      setTotal(res.total);
    } catch {
      setError("加载商品失败");
    } finally {
      setLoading(false);
    }
  }, [page]);

  useEffect(() => {
    loadProducts();
  }, [loadProducts]);

  function resetForm() {
    setForm({ ...emptyForm });
    setEditingId(null);
  }

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError(null);
    try {
      if (editingId === null) {
        await createCmsProduct(client, { ...form, price: Number(form.price) || 0 });
      } else {
        await updateCmsProduct(client, editingId, { ...form, price: Number(form.price) || 0 });
      }
      resetForm();
      await loadProducts();
    } catch {
      setError("保存商品失败");
    }
  }

  async function handleDelete(id: number) {
    if (!confirm("确认删除该商品?")) return;
    try {
      await deleteCmsProduct(client, id);
      await loadProducts();
    } catch {
      setError("删除商品失败");
    }
  }

  function handleEdit(item: CmsProduct) {
    setEditingId(item.id);
    setForm({
      title: item.title,
      image_url: item.image_url,
      price: item.price,
      status: item.status,
      sort_order: item.sort_order,
    });
  }

  const totalPages = Math.max(1, Math.ceil(total / PAGE_SIZE));

  return (
    <section className="space-y-6">
      <h1 className="text-2xl font-semibold">商品管理</h1>

      {error && <p className="text-sm text-red-600">{error}</p>}

      <form onSubmit={handleSubmit} className="space-y-3 rounded-lg border p-4">
        <div className="flex flex-wrap items-end gap-3">
          <div>
            <label className="mb-1 block text-xs text-muted-foreground">标题</label>
            <Input
              value={form.title}
              onChange={(e) => setForm({ ...form, title: e.target.value })}
              placeholder="商品标题"
              className="w-52"
            />
          </div>
          <div>
            <label className="mb-1 block text-xs text-muted-foreground">图片 URL</label>
            <Input
              value={form.image_url}
              onChange={(e) => setForm({ ...form, image_url: e.target.value })}
              placeholder="https://..."
              className="w-72"
            />
          </div>
          <div>
            <label className="mb-1 block text-xs text-muted-foreground">价格(分)</label>
            <Input
              type="number"
              value={form.price}
              onChange={(e) => setForm({ ...form, price: Number(e.target.value) })}
              className="w-28"
            />
          </div>
          <select
            value={form.status}
            onChange={(e) => setForm({ ...form, status: e.target.value })}
            className={selectClassName}
          >
            <option value="active">上架</option>
            <option value="inactive">下架</option>
          </select>
          <Button type="submit">{editingId === null ? "新增" : "更新"}</Button>
          {editingId !== null && (
            <Button type="button" variant="outline" onClick={resetForm}>
              取消
            </Button>
          )}
        </div>
      </form>

      {loading ? (
        <div className="flex items-center justify-center py-12">
          <Loader2 className="size-6 animate-spin text-muted-foreground" />
        </div>
      ) : items.length === 0 ? (
        <p className="py-8 text-center text-sm text-muted-foreground">暂无商品</p>
      ) : (
        <div className="overflow-hidden rounded-lg border">
          <table className="w-full text-sm">
            <thead className="bg-muted/50">
              <tr>
                <th className="px-4 py-3 text-left font-medium">ID</th>
                <th className="px-4 py-3 text-left font-medium">标题</th>
                <th className="px-4 py-3 text-left font-medium">价格</th>
                <th className="px-4 py-3 text-left font-medium">状态</th>
                <th className="px-4 py-3 text-right font-medium">操作</th>
              </tr>
            </thead>
            <tbody className="divide-y">
              {items.map((item) => (
                <tr key={item.id} className="hover:bg-muted/30">
                  <td className="px-4 py-3">{item.id}</td>
                  <td className="px-4 py-3 font-medium">{item.title}</td>
                  <td className="px-4 py-3">¥{(item.price / 100).toFixed(2)}</td>
                  <td className="px-4 py-3">
                    {item.status === "active" ? (
                      <span className="inline-block rounded-full bg-green-100 px-2.5 py-0.5 text-xs text-green-700">
                        上架
                      </span>
                    ) : (
                      <span className="inline-block rounded-full bg-gray-100 px-2.5 py-0.5 text-xs text-gray-600">
                        下架
                      </span>
                    )}
                  </td>
                  <td className="px-4 py-3 text-right">
                    <button onClick={() => handleEdit(item)} className="mr-2 text-blue-600 hover:underline" aria-label="编辑">
                      <Pencil className="inline size-4" />
                    </button>
                    <button onClick={() => handleDelete(item.id)} className="text-red-600 hover:underline" aria-label="删除">
                      <Trash2 className="inline size-4" />
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {!loading && items.length > 0 && (
        <div className="flex items-center justify-between text-sm text-muted-foreground">
          <span>
            共 {total} 条,第 {page} / {totalPages} 页
          </span>
          <div className="flex items-center gap-2">
            <Button variant="outline" size="sm" disabled={page <= 1} onClick={() => setPage((p) => p - 1)}>
              上一页
            </Button>
            <Button variant="outline" size="sm" disabled={page >= totalPages} onClick={() => setPage((p) => p + 1)}>
              下一页
            </Button>
          </div>
        </div>
      )}
    </section>
  );
}
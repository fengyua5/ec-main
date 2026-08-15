"use client";

import { useEffect, useState, useCallback } from "react";
import { Loader2, ArrowUp, ArrowDown, Pencil, Trash2, Plus } from "lucide-react";
import { createApiClient } from "@ec/sdk/client";
import {
  getCmsModules,
  createCmsModule,
  updateCmsModule,
  deleteCmsModule,
  moveCmsModule,
} from "@ec/sdk";
import type { CmsModule, ModuleInput } from "@ec/sdk";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Dialog } from "@/components/ui/dialog";

const client = createApiClient({
  baseUrl: process.env.NEXT_PUBLIC_API_URL || "",
});

const MODULE_TYPE_LABELS: Record<string, string> = {
  banner: "Banner 轮播",
  product_recommend: "推荐商品",
  announcement: "平台公告",
  search_bar: "搜索栏",
};

const DEFAULT_URLS: Record<string, string> = {
  banner: "/api/v1/web/home/banner",
  product_recommend: "/api/v1/web/home/products?status=active",
  announcement: "/api/v1/web/home/announcement",
  search_bar: "",
};

const emptyForm: ModuleInput = {
  module_type: "banner",
  title: "",
  description: "",
  data_source_url: DEFAULT_URLS.banner,
  is_static: false,
  sort_order: 0,
  is_enabled: true,
};

const selectClassName =
  "h-8 rounded-lg border border-input bg-transparent px-2.5 text-sm outline-none focus-visible:border-ring focus-visible:ring-3 focus-visible:ring-ring/50";

export default function ModulesPage() {
  const [modules, setModules] = useState<CmsModule[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [form, setForm] = useState<ModuleInput>({ ...emptyForm });
  const [editingId, setEditingId] = useState<number | null>(null);
  const [dialogOpen, setDialogOpen] = useState(false);

  const loadModules = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      setModules(await getCmsModules(client));
    } catch {
      setError("加载首页模块失败");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    loadModules();
  }, [loadModules]);

  function openCreateDialog() {
    setForm({ ...emptyForm });
    setEditingId(null);
    setDialogOpen(true);
  }

  function openEditDialog(module: CmsModule) {
    setEditingId(module.id);
    setForm({
      module_type: module.module_type,
      title: module.title,
      description: module.description,
      data_source_url: module.data_source_url,
      is_static: module.is_static,
      sort_order: module.sort_order,
      is_enabled: module.is_enabled,
    });
    setDialogOpen(true);
  }

  function closeDialog() {
    setDialogOpen(false);
    setEditingId(null);
  }

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError(null);
    try {
      if (editingId === null) {
        await createCmsModule(client, form);
      } else {
        await updateCmsModule(client, editingId, form);
      }
      closeDialog();
      await loadModules();
    } catch {
      setError("保存模块失败");
    }
  }

  async function handleDelete(id: number) {
    if (!confirm("确认删除该模块?")) return;
    try {
      await deleteCmsModule(client, id);
      await loadModules();
    } catch {
      setError("删除模块失败");
    }
  }

  async function handleMove(id: number, direction: "up" | "down") {
    try {
      setModules(await moveCmsModule(client, id, direction));
    } catch {
      setError("移动模块失败");
    }
  }

  return (
    <section className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-semibold">首页模块配置</h1>
        <Button onClick={openCreateDialog}>
          <Plus className="mr-1 size-4" />
          新增模块
        </Button>
      </div>

      {error && <p className="text-sm text-red-600">{error}</p>}

      {/* 新增/编辑弹窗 */}
      <Dialog open={dialogOpen} onClose={closeDialog} title={editingId === null ? "新增模块" : "编辑模块"}>
        <form onSubmit={handleSubmit} className="space-y-4">
          <div className="space-y-1.5">
            <Label>组件类型</Label>
            <select
              value={form.module_type}
              onChange={(e) => {
                const mt = e.target.value as ModuleInput["module_type"];
                const isStatic = mt === "search_bar";
                setForm({
                  ...form,
                  module_type: mt,
                  data_source_url: isStatic ? "" : DEFAULT_URLS[mt] ?? form.data_source_url,
                  is_static: isStatic,
                });
              }}
              className={selectClassName + " w-full"}
            >
              {Object.entries(MODULE_TYPE_LABELS).map(([value, label]) => (
                <option key={value} value={value}>
                  {label}
                </option>
              ))}
            </select>
          </div>

          <div className="space-y-1.5">
            <Label>名称</Label>
            <Input
              value={form.title}
              onChange={(e) => setForm({ ...form, title: e.target.value })}
              placeholder="模块名称"
            />
          </div>

          <div className="space-y-1.5">
            <Label>描述</Label>
            <Input
              value={form.description}
              onChange={(e) => setForm({ ...form, description: e.target.value })}
              placeholder="模块描述"
            />
          </div>

          <div className="space-y-1.5">
            <Label>API 地址</Label>
            <Input
              value={form.data_source_url}
              onChange={(e) => setForm({ ...form, data_source_url: e.target.value })}
              placeholder="数据源 URL"
              disabled={form.is_static}
            />
            {form.is_static && (
              <p className="text-xs text-muted-foreground">静态数据源无需 API 地址</p>
            )}
          </div>

          <div className="flex items-center gap-2">
            <input
              id="is_static"
              type="checkbox"
              checked={form.is_static}
              onChange={(e) => setForm({ ...form, is_static: e.target.checked })}
              className="size-4"
            />
            <Label htmlFor="is_static">静态数据源</Label>
          </div>

          <div className="flex items-center gap-2">
            <input
              id="is_enabled"
              type="checkbox"
              checked={form.is_enabled}
              onChange={(e) => setForm({ ...form, is_enabled: e.target.checked })}
              className="size-4"
            />
            <Label htmlFor="is_enabled">启用</Label>
          </div>

          <div className="flex justify-end gap-2 pt-2">
            <Button type="button" variant="outline" onClick={closeDialog}>
              取消
            </Button>
            <Button type="submit">{editingId === null ? "新增" : "更新"}</Button>
          </div>
        </form>
      </Dialog>

      {/* 模块列表 */}
      {loading ? (
        <div className="flex items-center justify-center py-12">
          <Loader2 className="size-6 animate-spin text-muted-foreground" />
        </div>
      ) : modules.length === 0 ? (
        <p className="py-8 text-center text-sm text-muted-foreground">暂无模块</p>
      ) : (
        <table className="w-full overflow-hidden rounded-lg border text-sm">
          <thead className="bg-muted/50">
            <tr>
              <th className="px-4 py-3 text-left font-medium">排序</th>
              <th className="px-4 py-3 text-left font-medium">类型</th>
              <th className="px-4 py-3 text-left font-medium">名称</th>
              <th className="px-4 py-3 text-left font-medium">描述</th>
              <th className="px-4 py-3 text-left font-medium">数据源</th>
              <th className="px-4 py-3 text-left font-medium">状态</th>
              <th className="px-4 py-3 text-right font-medium">操作</th>
            </tr>
          </thead>
          <tbody className="divide-y">
            {modules.map((module) => (
              <tr key={module.id} className="hover:bg-muted/30">
                <td className="px-4 py-3">
                  <div className="flex items-center gap-1">
                    <button
                      onClick={() => handleMove(module.id, "up")}
                      disabled={module.sort_order === 0}
                      className="text-muted-foreground hover:text-foreground disabled:opacity-40"
                      aria-label="上移"
                    >
                      <ArrowUp className="size-4" />
                    </button>
                    <button
                      onClick={() => handleMove(module.id, "down")}
                      className="text-muted-foreground hover:text-foreground"
                      aria-label="下移"
                    >
                      <ArrowDown className="size-4" />
                    </button>
                  </div>
                </td>
                <td className="px-4 py-3">
                  {MODULE_TYPE_LABELS[module.module_type] ?? module.module_type}
                </td>
                <td className="px-4 py-3">{module.title}</td>
                <td className="px-4 py-3 text-xs text-muted-foreground">
                  {module.description || "-"}
                </td>
                <td className="px-4 py-3 font-mono text-xs text-muted-foreground">
                  {module.is_static ? (
                    <span className="text-green-600">静态数据</span>
                  ) : (
                    module.data_source_url
                  )}
                </td>
                <td className="px-4 py-3">
                  {module.is_enabled ? (
                    <span className="inline-block rounded-full bg-green-100 px-2.5 py-0.5 text-xs text-green-700">
                      启用
                    </span>
                  ) : (
                    <span className="inline-block rounded-full bg-gray-100 px-2.5 py-0.5 text-xs text-gray-600">
                      停用
                    </span>
                  )}
                </td>
                <td className="px-4 py-3 text-right">
                  <button onClick={() => openEditDialog(module)} className="mr-2 text-blue-600 hover:underline" aria-label="编辑">
                    <Pencil className="inline size-4" />
                  </button>
                  <button onClick={() => handleDelete(module.id)} className="text-red-600 hover:underline" aria-label="删除">
                    <Trash2 className="inline size-4" />
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </section>
  );
}
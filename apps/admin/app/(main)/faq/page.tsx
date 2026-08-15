"use client";

import { useEffect, useState, useCallback } from "react";
import { createApiClient } from "@ec/sdk/client";
import {
  getFAQDocuments,
  uploadFAQDocument,
  deleteFAQDocument,
} from "@ec/sdk";
import type { FAQDocument } from "@ec/sdk";
import { UploadForm } from "./components/upload-form";
import { Button } from "@/components/ui/button";
import { Trash2, Loader2 } from "lucide-react";

const client = createApiClient({
  baseUrl: process.env.NEXT_PUBLIC_API_URL || "",
});

export default function FAQPage() {
  const [documents, setDocuments] = useState<FAQDocument[]>([]);
  const [loading, setLoading] = useState(true);
  const [uploading, setUploading] = useState(false);
  const [deletingId, setDeletingId] = useState<number | null>(null);
  const [feedback, setFeedback] = useState<{
    type: "success" | "error";
    message: string;
  } | null>(null);

  const loadDocuments = useCallback(async () => {
    setLoading(true);
    try {
      const docs = await getFAQDocuments(client);
      setDocuments(docs);
      setFeedback(null);
    } catch {
      setFeedback({ type: "error", message: "加载 FAQ 文档失败" });
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    loadDocuments();
  }, [loadDocuments]);

  async function handleUpload(file: File) {
    if (!file.name.endsWith(".md")) {
      setFeedback({ type: "error", message: "仅支持 .md 文件" });
      return;
    }
    setUploading(true);
    setFeedback(null);
    try {
      await uploadFAQDocument(client, file);
      setFeedback({ type: "success", message: "上传成功" });
      await loadDocuments();
    } catch {
      setFeedback({ type: "error", message: "上传失败" });
    } finally {
      setUploading(false);
    }
  }

  async function handleDelete(id: number) {
    if (!confirm("确定要删除该文档吗？")) return;
    setDeletingId(id);
    try {
      await deleteFAQDocument(client, id);
      setDocuments((prev) => prev.filter((d) => d.id !== id));
      setFeedback({ type: "success", message: "删除成功" });
    } catch {
      setFeedback({ type: "error", message: "删除失败" });
    } finally {
      setDeletingId(null);
    }
  }

  return (
    <section className="space-y-6">
      <h1 className="text-2xl font-semibold">FAQ 管理</h1>

      {uploading ? (
        <div className="flex items-center justify-center gap-2 rounded-lg border-2 border-dashed border-gray-300 p-8 text-sm text-muted-foreground">
          <Loader2 className="size-5 animate-spin" />
          正在上传...
        </div>
      ) : (
        <UploadForm onUpload={handleUpload} />
      )}

      {feedback && (
        <p
          className={`text-sm ${feedback.type === "success" ? "text-green-600" : "text-red-600"}`}
        >
          {feedback.message}
        </p>
      )}

      {loading ? (
        <div className="flex items-center justify-center py-12">
          <Loader2 className="size-6 animate-spin text-muted-foreground" />
        </div>
      ) : documents.length === 0 ? (
        <p className="py-8 text-center text-sm text-muted-foreground">
          暂无 FAQ 文档
        </p>
      ) : (
        <div className="overflow-hidden rounded-lg border">
          <table className="w-full text-sm">
            <thead className="bg-muted/50">
              <tr>
                <th className="px-4 py-3 text-left font-medium">文件名</th>
                <th className="px-4 py-3 text-left font-medium">切片数</th>
                <th className="px-4 py-3 text-left font-medium">上传时间</th>
                <th className="px-4 py-3 text-right font-medium">操作</th>
              </tr>
            </thead>
            <tbody className="divide-y">
              {documents.map((doc) => (
                <tr key={doc.id} className="hover:bg-muted/30">
                  <td className="px-4 py-3">{doc.filename}</td>
                  <td className="px-4 py-3">{doc.chunk_count}</td>
                  <td className="px-4 py-3">
                    {new Date(doc.created_at).toLocaleString("zh-CN")}
                  </td>
                  <td className="px-4 py-3 text-right">
                    <Button
                      variant="ghost"
                      size="icon"
                      disabled={deletingId === doc.id}
                      onClick={() => handleDelete(doc.id)}
                    >
                      {deletingId === doc.id ? (
                        <Loader2 className="size-4 animate-spin" />
                      ) : (
                        <Trash2 className="size-4 text-red-500" />
                      )}
                    </Button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </section>
  );
}

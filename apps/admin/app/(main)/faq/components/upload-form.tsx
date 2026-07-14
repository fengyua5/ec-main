"use client";

import { useState, useRef, type DragEvent } from "react";
import { Upload } from "lucide-react";
import { cn } from "@/lib/utils";

type UploadFormProps = {
  onUpload: (file: File) => Promise<void>;
};

export function UploadForm({ onUpload }: UploadFormProps) {
  const [dragging, setDragging] = useState(false);
  const inputRef = useRef<HTMLInputElement>(null);

  function handleDragOver(e: DragEvent) {
    e.preventDefault();
    setDragging(true);
  }

  function handleDragLeave() {
    setDragging(false);
  }

  function handleDrop(e: DragEvent) {
    e.preventDefault();
    setDragging(false);
    const file = e.dataTransfer.files[0];
    if (file) onUpload(file);
  }

  function handleFileChange(e: React.ChangeEvent<HTMLInputElement>) {
    const file = e.target.files?.[0];
    if (file) onUpload(file);
  }

  return (
    <div
      onDragOver={handleDragOver}
      onDragLeave={handleDragLeave}
      onDrop={handleDrop}
      onClick={() => inputRef.current?.click()}
      className={cn(
        "flex cursor-pointer flex-col items-center justify-center rounded-lg border-2 border-dashed p-8 text-sm text-muted-foreground transition-colors",
        dragging
          ? "border-blue-500 bg-blue-50 text-blue-600"
          : "border-gray-300 hover:border-gray-400 hover:bg-gray-50",
      )}
    >
      <Upload className="mb-2 size-6" />
      <span>拖拽或点击上传 Markdown 文件</span>
      <input
        ref={inputRef}
        type="file"
        accept=".md,.markdown"
        className="hidden"
        onChange={handleFileChange}
      />
    </div>
  );
}

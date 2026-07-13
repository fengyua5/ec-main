import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "EC Main Admin",
  description: "电商 MVP Admin 后台底座"
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="zh-CN">
      <body>{children}</body>
    </html>
  );
}

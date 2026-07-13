import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "EC Main 买家端",
  description: "电商 MVP 买家端底座"
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="zh-CN">
      <body>{children}</body>
    </html>
  );
}

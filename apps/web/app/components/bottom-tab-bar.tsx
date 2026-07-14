"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { Home, Bot, User } from "lucide-react";

const tabs = [
  { href: "/", label: "首页", Icon: Home },
  { href: "/ai", label: "AI 客服", Icon: Bot },
  { href: "/account", label: "账号", Icon: User },
];

export function BottomTabBar() {
  const pathname = usePathname();

  return (
    <nav className="fixed bottom-0 left-0 right-0 z-50 flex h-16 items-center justify-around border-t bg-background">
      {tabs.map(({ href, label, Icon }) => {
        const isActive = pathname === href;
        return (
          <Link
            key={href}
            href={href}
            className={`flex flex-col items-center gap-0.5 text-xs ${
              isActive ? "text-primary" : "text-muted-foreground"
            }`}
          >
            <Icon className="size-5" />
            <span>{label}</span>
          </Link>
        );
      })}
    </nav>
  );
}

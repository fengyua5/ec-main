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
    <nav className="fixed bottom-0 left-0 right-0 z-50 flex h-16 items-center border-t bg-white">
      {tabs.map(({ href, label, Icon }) => {
        const isActive = pathname === href;
        return (
          <Link
            key={href}
            href={href}
            className="relative flex flex-1 flex-col items-center justify-center gap-0.5 text-xs text-muted-foreground"
          >
            {isActive && (
              <span className="absolute -top-0 left-1/2 h-1 w-8 -translate-x-1/2 rounded-full bg-primary" />
            )}
            <Icon className={`size-5 ${isActive ? "text-primary" : ""}`} />
            <span className={isActive ? "font-medium text-primary" : ""}>{label}</span>
          </Link>
        );
      })}
    </nav>
  );
}

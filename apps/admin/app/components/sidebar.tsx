"use client";

import { usePathname } from "next/navigation";
import { Separator } from "@/components/ui/separator";

const navItems = [
  { label: "概览", href: "/" },
  { label: "FAQ 管理", href: "/faq" },
  { label: "客服消息", href: "/chat" },
  { label: "订单管理", href: "/orders" },
  { label: "商品管理", href: "/products" },
  { label: "用户管理", href: "/users" },
];

function isActive(pathname: string, href: string) {
  if (href === "/") {
    return pathname === "/";
  }
  return pathname === href || pathname.startsWith(`${href}/`);
}

export function Sidebar() {
  const pathname = usePathname();

  return (
    <aside className="w-56 shrink-0 border-r bg-muted/30 p-4">
      <nav className="space-y-1">
        {navItems.map((item) => {
          const active = isActive(pathname, item.href);
          return (
            <a
              key={item.href}
              href={item.href}
              aria-current={active ? "page" : undefined}
              className={`block rounded-md px-3 py-2 text-sm hover:bg-accent hover:text-accent-foreground ${
                active ? "bg-accent text-accent-foreground font-medium" : "text-muted-foreground"
              }`}
            >
              {item.label}
            </a>
          );
        })}
      </nav>
      <Separator className="my-4" />
      <p className="px-3 text-xs text-muted-foreground">EC Main Admin v0.1</p>
    </aside>
  );
}

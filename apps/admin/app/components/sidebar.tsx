import { Separator } from "@/components/ui/separator";

const navItems = [
  { label: "概览", href: "/" },
  { label: "订单管理", href: "/orders" },
  { label: "商品管理", href: "/products" },
  { label: "用户管理", href: "/users" },
];

export function Sidebar() {
  return (
    <aside className="w-56 shrink-0 border-r bg-muted/30 p-4">
      <nav className="space-y-1">
        {navItems.map((item) => (
          <a
            key={item.href}
            href={item.href}
            className="block rounded-md px-3 py-2 text-sm text-muted-foreground hover:bg-accent hover:text-accent-foreground"
          >
            {item.label}
          </a>
        ))}
      </nav>
      <Separator className="my-4" />
      <p className="px-3 text-xs text-muted-foreground">EC Main Admin v0.1</p>
    </aside>
  );
}

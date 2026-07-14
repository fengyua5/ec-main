"use client";

import { useEffect, useState } from "react";
import { Button } from "@/components/ui/button";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import { Avatar, AvatarFallback } from "@/components/ui/avatar";

type User = {
  id: number;
  username: string | null;
  email: string;
  role: string;
};

export function AdminAuthHeader() {
  const [user, setUser] = useState<User | null>(null);

  useEffect(() => {
    fetch("/api/auth/me")
      .then((res) => (res.ok ? res.json() : null))
      .then((data) => setUser(data))
      .catch(() => setUser(null));
  }, []);

  async function handleLogout() {
    await fetch("/api/auth/logout", { method: "POST" });
    setUser(null);
  }

  return (
    <header className="flex h-14 items-center justify-between border-b px-6">
      <a href="/" className="text-lg font-bold">EC Main Admin</a>
      <div className="flex items-center gap-4">
        {user ? (
          <DropdownMenu>
            <DropdownMenuTrigger>
              <Button variant="ghost" className="flex items-center gap-2">
                <Avatar className="size-8">
                  <AvatarFallback>{(user.username ?? user.email)[0].toUpperCase()}</AvatarFallback>
                </Avatar>
                <span className="text-sm">{user.username ?? user.email}</span>
              </Button>
            </DropdownMenuTrigger>
            <DropdownMenuContent align="end">
              <DropdownMenuItem onClick={handleLogout}>登出</DropdownMenuItem>
            </DropdownMenuContent>
          </DropdownMenu>
        ) : (
          <>
            <a href="/login" className="text-sm text-muted-foreground hover:text-foreground">登录</a>
            <a href="/register">
              <Button>注册</Button>
            </a>
          </>
        )}
      </div>
    </header>
  );
}

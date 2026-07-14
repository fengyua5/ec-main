import { BottomTabBar } from "@/app/components/bottom-tab-bar";

export default function MainLayout({ children }: { children: React.ReactNode }) {
  return (
    <>
      <main className="mx-auto max-w-5xl p-6 pb-24">{children}</main>
      <BottomTabBar />
    </>
  );
}

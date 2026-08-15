import { createApiClient, checkHealth } from "@ec/sdk";
import { Button } from "@/components/ui/button";

const apiBaseUrl = process.env.NEXT_PUBLIC_API_BASE_URL ?? "";

async function getHealthLabel() {
  try {
    const client = createApiClient({ baseUrl: apiBaseUrl });
    const health = await checkHealth(client);
    return `${health.service}: ${health.status}`;
  } catch {
    return "backend: unavailable";
  }
}

export default async function AdminHomePage() {
  const healthLabel = await getHealthLabel();

  return (
    <section className="flex flex-col gap-8">
      <div className="space-y-3">
        <p className="text-sm font-medium uppercase tracking-wide text-zinc-500">EC Main Admin</p>
        <h1 className="text-4xl font-semibold">Admin 后台底座</h1>
        <p className="max-w-2xl text-base leading-7 text-zinc-600">
          这里是电商 MVP 的后台入口，后续会承载商品维护、上下架、价格和库存基础管理。
        </p>
      </div>
      <div className="flex items-center gap-4">
        <Button variant="secondary">后台底座已就绪</Button>
        <span className="text-sm text-zinc-500">{healthLabel}</span>
      </div>
    </section>
  );
}

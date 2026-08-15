import { createApiClient, checkHealth } from "@ec/sdk";
import { Button } from "@/components/ui/button";

const apiBaseUrl = process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000";

async function getHealthLabel() {
  try {
    const client = createApiClient({ baseUrl: apiBaseUrl });
    const health = await checkHealth(client);
    return `${health.service}: ${health.status}`;
  } catch {
    return "backend: unavailable";
  }
}

export default async function HomePage() {
  const healthLabel = await getHealthLabel();

  return (
    <div className="min-h-screen bg-surface-200-bg px-6 py-10 text-surface-100-fg-default">
      <section className="mx-auto flex max-w-5xl flex-col gap-8">
        <div className="space-y-3">
          <p className="enki-body-sm font-medium uppercase tracking-wide text-surface-100-fg-minor">
            EC Main
          </p>
          <h1 className="enki-heading-3xl">买家端商城底座</h1>
          <p className="enki-body-base text-surface-100-fg-minor">
            这里是电商 MVP 的买家端入口，后续会承载首页、PDP、购物车、结算和订单体验。
          </p>
        </div>
        <div className="flex items-center gap-4">
          <Button>平台底座已就绪</Button>
          <span className="text-sm text-surface-100-fg-minor">{healthLabel}</span>
        </div>
      </section>
    </div>
  );
}

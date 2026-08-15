import { createApiClient, getHomeModules, type HomeModule } from "@ec/sdk";
import { HomeModuleRenderer } from "./components/home-module-renderer";

const apiBaseUrl = process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000";

async function loadHomeData(): Promise<{ modules: HomeModule[]; staticData: Record<number, unknown> } | null> {
  try {
    const client = createApiClient({ baseUrl: apiBaseUrl });
    const { modules } = await getHomeModules(client);

    const staticData: Record<number, unknown> = {};
    const staticModules = modules.filter((m) => m.is_static && m.data_source_url);

    await Promise.all(
      staticModules.map(async (m) => {
        const data = await client.request<unknown>(m.data_source_url);
        staticData[m.id] = data;
      }),
    );

    return { modules, staticData };
  } catch {
    return null;
  }
}

export default async function HomePage() {
  const result = await loadHomeData();

  return (
    <div className="min-h-screen bg-surface-100-bg text-surface-100-fg-default">
      <main className="mx-auto flex max-w-5xl flex-col">
        {result ? (
          <HomeModuleRenderer modules={result.modules} staticData={result.staticData} />
        ) : (
          <p className="enki-body-base text-surface-100-fg-minor">
            首页模块加载失败，请先到 Admin 后台配置首页内容。
          </p>
        )}
      </main>
    </div>
  );
}
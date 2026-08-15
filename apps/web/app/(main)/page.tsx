import { createApiClient, getHomeModules, getHomeBanner, getHomeAnnouncements, getPublicProducts, type HomeModule } from "@ec/sdk";
import { HomeModuleRenderer, type ModulePayloads } from "./components/home-module-renderer";

const apiBaseUrl = process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000";

async function loadHomeData(): Promise<{ modules: HomeModule[]; staticData: Partial<ModulePayloads> } | null> {
  try {
    const client = createApiClient({ baseUrl: apiBaseUrl });
    const { modules } = await getHomeModules(client);

    const staticData: Partial<ModulePayloads> = {};
    const types = new Set(modules.filter((m) => m.is_static && m.data_source_url).map((m) => m.module_type));

    const promises: Promise<void>[] = [];
    if (types.has("banner")) {
      promises.push(
        getHomeBanner(client).then((res) => { staticData.banner = res.items; }),
      );
    }
    if (types.has("product_recommend")) {
      promises.push(
        getPublicProducts(client, { status: "active" }).then((res) => { staticData.product_recommend = res.items; }),
      );
    }
    if (types.has("announcement")) {
      promises.push(
        getHomeAnnouncements(client).then((res) => { staticData.announcement = res.items; }),
      );
    }

    await Promise.all(promises);
    return { modules, staticData };
  } catch {
    return null;
  }
}

export default async function HomePage() {
  const result = await loadHomeData();

  return (
    <div className="min-h-screen bg-surface-200-bg text-surface-100-fg-default">
      <main className="mx-auto flex max-w-5xl flex-col gap-8">
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
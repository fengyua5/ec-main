import {
  createApiClient,
  getHomeModules,
  getHomeBanner,
  getHomeAnnouncements,
  getPublicProducts,
  type HomeModule,
} from "@ec/sdk";
import { HomeModuleRenderer, type ModulePayloads } from "./components/home-module-renderer";

const apiBaseUrl = process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000";

type HomeData =
  | { modules: HomeModule[]; data: ModulePayloads }
  | { modules: null; data: null };

async function loadHomeData(): Promise<HomeData> {
  try {
    const client = createApiClient({ baseUrl: apiBaseUrl });
    const [moduleRes, bannerRes, annoRes, productsRes] = await Promise.all([
      getHomeModules(client),
      getHomeBanner(client),
      getHomeAnnouncements(client),
      getPublicProducts(client, { status: "active" }),
    ]);
    return {
      modules: moduleRes.modules,
      data: {
        banner: bannerRes.items,
        product_recommend: productsRes.items,
        announcement: annoRes.items,
      },
    };
  } catch {
    return { modules: null, data: null };
  }
}

export default async function HomePage() {
  const { modules, data } = await loadHomeData();

  return (
    <div className="min-h-screen bg-surface-200-bg px-6 py-10 text-surface-100-fg-default">
      <main className="mx-auto flex max-w-5xl flex-col gap-8">
        <section className="space-y-3">
          <p className="enki-body-sm font-medium uppercase tracking-wide text-surface-100-fg-minor">
            EC Main
          </p>
          <h1 className="enki-heading-3xl">买家端商城</h1>
        </section>

        {modules && data ? (
          <HomeModuleRenderer modules={modules} data={data} />
        ) : (
          <p className="enki-body-base text-surface-100-fg-minor">
            首页模块加载失败，请先到 Admin 后台配置首页内容。
          </p>
        )}
      </main>
    </div>
  );
}

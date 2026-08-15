import type { HomeModule, BannerItem, Product, Announcement } from "@ec/sdk";
import { CmsBanner, CmsProductGrid, CmsAnnouncement, CmsSearchBar } from "../cms-components";
import { DynamicCmsModule } from "./dynamic-cms-module";

export type ModulePayloads = {
  banner: BannerItem[];
  product_recommend: Product[];
  announcement: Announcement[];
};

type Props = {
  modules: HomeModule[];
  staticData: Partial<ModulePayloads>;
};

export function HomeModuleRenderer({ modules, staticData }: Props) {
  return (
    <div className="space-y-8">
      {modules.map((module) => {
        if (module.is_static) {
          switch (module.module_type) {
            case "banner":
              return <CmsBanner key={module.id} items={staticData.banner ?? []} />;
            case "product_recommend":
              return <CmsProductGrid key={module.id} items={staticData.product_recommend ?? []} />;
            case "announcement":
              return <CmsAnnouncement key={module.id} items={staticData.announcement ?? []} />;
            case "search_bar":
              return <CmsSearchBar key={module.id} />;
            default:
              return null;
          }
        }
        return <DynamicCmsModule key={module.id} module={module} />;
      })}
    </div>
  );
}
import type { HomeModule, BannerItem, Product, Announcement } from "@ec/sdk";
import { CmsBanner, CmsProductWaterfall, CmsProductList, CmsAnnouncement, CmsSearchBar } from "../cms-components";
import { DynamicCmsModule } from "./dynamic-cms-module";

type Props = {
  modules: HomeModule[];
  staticData: Record<number, unknown>;
};

export function HomeModuleRenderer({ modules, staticData }: Props) {
  return (
    <div className="">
      {modules.map((module) => {
        if (module.is_static) {
          switch (module.module_type) {
            case "banner":
              return <CmsBanner key={module.id} items={(staticData[module.id] as { items: BannerItem[] } | undefined)?.items ?? []} />;
            case "product_recommend":
              return <CmsProductWaterfall key={module.id} title={module.title} items={(staticData[module.id] as { items: Product[] } | undefined)?.items ?? []} />;
            case "product_list":
              return <CmsProductList key={module.id} title={module.title} items={(staticData[module.id] as { items: Product[] } | undefined)?.items ?? []} />;
            case "announcement":
              return <CmsAnnouncement key={module.id} items={(staticData[module.id] as { items: Announcement[] } | undefined)?.items ?? []} />;
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
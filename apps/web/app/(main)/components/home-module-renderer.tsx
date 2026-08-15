import { HomeModule, BannerItem, Product, Announcement } from "@ec/sdk";
import { HomeBanner } from "./home-banner";
import { HomeProductGrid } from "./home-product-grid";
import { HomeAnnouncement } from "./home-announcement";

export type ModulePayloads = {
  banner: BannerItem[];
  product_recommend: Product[];
  announcement: Announcement[];
};

type Props = {
  modules: HomeModule[];
  data: ModulePayloads;
};

export function HomeModuleRenderer({ modules, data }: Props) {
  return (
    <div className="space-y-8">
      {modules.map((module) => {
        const key = module.id;
        switch (module.module_type) {
          case "banner":
            return <HomeBanner key={key} items={data.banner} />;
          case "product_recommend":
            return <HomeProductGrid key={key} items={data.product_recommend} />;
          case "announcement":
            return <HomeAnnouncement key={key} items={data.announcement} />;
          default:
            return null;
        }
      })}
    </div>
  );
}
import { render, screen, cleanup } from "@testing-library/react";
import { afterEach, describe, it, expect } from "vitest";
import { CmsSearchBar } from "@/app/(main)/cms-components/cms-search-bar";

afterEach(cleanup);

describe("CmsSearchBar", () => {
  it("renders search input", () => {
    render(<CmsSearchBar />);
    expect(screen.getByPlaceholderText("搜索商品…")).toBeInTheDocument();
  });
});
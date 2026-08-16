import { render, screen, cleanup } from "@testing-library/react";
import { afterEach, describe, it, expect } from "vitest";
import { CmsBanner } from "@/app/(main)/cms-components/cms-banner";

afterEach(cleanup);

describe("CmsBanner", () => {
  it("renders nothing when empty", () => {
    const { container } = render(<CmsBanner items={[]} />);
    expect(container.innerHTML).toBe("");
  });

  it("renders banner images", () => {
    render(
      <CmsBanner
        items={[
          { id: 1, image_url: "https://example.com/b1.jpg", description: "", link_url: "" },
          { id: 2, image_url: "https://example.com/b2.jpg", description: "", link_url: "/p/2" },
        ]}
      />,
    );
    expect(screen.getAllByAltText("banner")).toHaveLength(2);
  });

  it("renders link when link_url is present", () => {
    render(
      <CmsBanner
        items={[{ id: 1, image_url: "https://example.com/b.jpg", description: "", link_url: "/target" }]}
      />,
    );
    const link = screen.getByAltText("banner").closest("a");
    expect(link).toHaveAttribute("href", "/target");
  });

  it("renders dot indicators for multiple items", () => {
    render(
      <CmsBanner
        items={[
          { id: 1, image_url: "https://example.com/b1.jpg", description: "", link_url: "" },
          { id: 2, image_url: "https://example.com/b2.jpg", description: "", link_url: "" },
        ]}
      />,
    );
    const dots = screen.getAllByRole("button");
    expect(dots.length).toBeGreaterThanOrEqual(2);
  });

  it("does not render dots for single item", () => {
    render(
      <CmsBanner
        items={[{ id: 1, image_url: "https://example.com/b.jpg", description: "", link_url: "" }]}
      />,
    );
    expect(screen.queryByRole("button")).not.toBeInTheDocument();
  });
});
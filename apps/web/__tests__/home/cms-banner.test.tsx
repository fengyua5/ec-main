import { render, screen, cleanup, act } from "@testing-library/react";
import { afterEach, describe, it, expect, vi, beforeEach, afterAll } from "vitest";
import { CmsBanner } from "@/app/(main)/cms-components/cms-banner";

afterEach(cleanup);

beforeEach(() => {
  vi.useFakeTimers();
});

afterAll(() => {
  vi.useRealTimers();
});

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
    expect(screen.getByAltText("banner-0")).toBeInTheDocument();
    expect(screen.getByAltText("banner-1")).toBeInTheDocument();
  });

  it("renders link when link_url is present", () => {
    render(
      <CmsBanner
        items={[{ id: 1, image_url: "https://example.com/b.jpg", description: "", link_url: "/target" }]}
      />,
    );
    const link = screen.getByAltText("banner-0").closest("a");
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
    expect(dots).toHaveLength(2);
  });

  it("does not render dots for single item", () => {
    render(
      <CmsBanner
        items={[{ id: 1, image_url: "https://example.com/b.jpg", description: "", link_url: "" }]}
      />,
    );
    expect(screen.queryByRole("button")).not.toBeInTheDocument();
  });

  it("auto-advances to next slide", () => {
    render(
      <CmsBanner
        items={[
          { id: 1, image_url: "https://example.com/b1.jpg", description: "", link_url: "" },
          { id: 2, image_url: "https://example.com/b2.jpg", description: "", link_url: "" },
        ]}
      />,
    );
    const dots = screen.getAllByRole("button");
    expect(dots[0]).toHaveClass("bg-white");
    expect(dots[1]).toHaveClass("bg-white/50");

    act(() => {
      vi.advanceTimersByTime(4000);
    });
    expect(dots[0]).toHaveClass("bg-white/50");
    expect(dots[1]).toHaveClass("bg-white");
  });
});
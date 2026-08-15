import { render, screen, cleanup } from "@testing-library/react";
import { afterEach, describe, it, expect } from "vitest";
import { CmsAnnouncement } from "@/app/(main)/cms-components/cms-announcement";

afterEach(cleanup);

describe("CmsAnnouncement", () => {
  it("renders nothing when empty", () => {
    const { container } = render(<CmsAnnouncement items={[]} />);
    expect(container.innerHTML).toBe("");
  });

  it("renders announcement content", () => {
    render(
      <CmsAnnouncement
        items={[
          { id: 1, content: "公告1" },
          { id: 2, content: "公告2" },
        ]}
      />,
    );
    expect(screen.getByText("公告1")).toBeInTheDocument();
    expect(screen.getByText("公告2")).toBeInTheDocument();
  });
});
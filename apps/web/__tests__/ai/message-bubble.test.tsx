import { render, screen, cleanup } from "@testing-library/react";
import { afterEach, describe, it, expect } from "vitest";
import { MessageBubble } from "@/app/(main)/ai/components/message-bubble";

afterEach(cleanup);

function makeAiMessage(content: string) {
  return {
    id: 1,
    conversation_id: 1,
    sender: "ai" as const,
    content,
    msg_type: "text" as const,
    created_at: new Date().toISOString(),
  };
}

describe("MessageBubble", () => {
  it("shows placeholder text while streaming an empty ai message", () => {
    render(<MessageBubble message={makeAiMessage("")} isStreaming />);
    expect(screen.getByText("正在查找中...")).toBeInTheDocument();
  });

  it("binds refs for direct dom streaming", () => {
    const contentRef = { current: null };
    const pendingTextRef = { current: null };
    render(
      <MessageBubble
        message={makeAiMessage("")}
        isStreaming
        contentRef={contentRef}
        pendingTextRef={pendingTextRef}
      />,
    );
    expect(contentRef.current).not.toBeNull();
    expect(pendingTextRef.current).not.toBeNull();
  });

  it("renders content once tokens arrive and hides placeholder", () => {
    render(<MessageBubble message={makeAiMessage("这是答案")} isStreaming />);
    expect(screen.getByText("这是答案")).toBeInTheDocument();
    expect(screen.queryByText(/正在查找中/)).not.toBeInTheDocument();
  });

  it("removes a hidden placeholder on rerender without throwing", () => {
    const { rerender } = render(
      <MessageBubble message={makeAiMessage("")} isStreaming />,
    );
    const placeholder = document.querySelector("[data-placeholder]");
    expect(placeholder).not.toBeNull();
    (placeholder as HTMLElement).style.display = "none";

    expect(() =>
      rerender(<MessageBubble message={makeAiMessage("内容")} />),
    ).not.toThrow();
    expect(screen.getByText("内容")).toBeInTheDocument();
  });
});

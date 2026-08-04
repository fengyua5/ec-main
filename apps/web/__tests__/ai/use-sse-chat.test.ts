import { renderHook, act } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { useSSEChat } from "@/app/(main)/ai/hooks/use-sse-chat";

type WorkerLike = {
  onmessage: ((e: MessageEvent) => void) | null;
  postMessage: ReturnType<typeof vi.fn>;
};

const workers: WorkerLike[] = [];

class MockWorker {
  onmessage: ((e: MessageEvent) => void) | null = null;
  postMessage = vi.fn();
  terminate = vi.fn();
  constructor() {
    workers.push(this);
  }
}

beforeEach(() => {
  vi.stubGlobal("Worker", MockWorker);
  workers.length = 0;
});

afterEach(() => {
  vi.unstubAllGlobals();
});

function emit(worker: WorkerLike, data: unknown) {
  act(() => {
    worker.onmessage?.({ data } as MessageEvent);
  });
}

describe("useSSEChat streaming", () => {
  it("posts chat request to worker with url and payload", () => {
    const { result } = renderHook(() => useSSEChat());
    const worker = workers[0];

    act(() => {
      result.current.sendMessage("hi");
    });

    expect(worker.postMessage).toHaveBeenCalledWith({
      url: expect.stringContaining("/api/v1/web/ai/chat"),
      payload: { conversation_id: null, content: "hi" },
    });
  });

  it("writes tokens to dom directly without syncing state, then syncs on done", () => {
    const { result } = renderHook(() => useSSEChat());
    const worker = workers[0];

    const bubble = document.createElement("div");
    const el = document.createElement("span");
    const placeholder = document.createElement("span");
    placeholder.setAttribute("data-placeholder", "");
    bubble.append(el, placeholder);
    (result.current.contentRef as { current: HTMLElement | null }).current = el;

    act(() => {
      result.current.sendMessage("hi");
    });

    emit(worker, { type: "status", content: "正在查找中..." });
    emit(worker, { type: "token", content: "你好" });
    emit(worker, { type: "token", content: "！" });

    const aiMsg = () =>
      result.current.messages[result.current.messages.length - 1];
    expect(el.textContent).toBe("你好！");
    expect(aiMsg().content).toBe("");
    expect(placeholder.style.display).toBe("none");
    expect(bubble.contains(placeholder)).toBe(true);

    emit(worker, { type: "done" });

    expect(aiMsg().content).toBe("你好！");
    expect(result.current.isStreaming).toBe(false);
  });

  it("shows fallback error message on worker error and drops empty placeholder", () => {
    const { result } = renderHook(() => useSSEChat());
    const worker = workers[0];

    act(() => {
      result.current.sendMessage("hi");
    });

    emit(worker, { type: "error" });

    const last = result.current.messages[result.current.messages.length - 1];
    expect(last.content).toBe("消息发送失败，请稍后重试");
    expect(result.current.isStreaming).toBe(false);
  });
});

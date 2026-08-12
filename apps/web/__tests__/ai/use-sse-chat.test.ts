import { renderHook, act } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { useSSEChat } from "@/app/(main)/ai/hooks/use-sse-chat";

vi.mock("@ec/sdk", async (importOriginal) => {
  const actual = await importOriginal<typeof import("@ec/sdk")>();
  return {
    ...actual,
    getConversations: vi.fn(),
    getMessages: vi.fn(),
  };
});

import { getConversations, getMessages } from "@ec/sdk";
import type { Message } from "@ec/sdk";

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

describe("useSSEChat history loading", () => {
  afterEach(() => {
    vi.clearAllMocks();
  });

  function makeMsg(
    id: number,
    conversation_id: number,
    content: string,
    created_at = "2026-08-12T00:00:00Z",
  ): Message {
    return {
      id,
      conversation_id,
      sender: "ai",
      content,
      msg_type: "text",
      created_at,
    };
  }

  const CONV_2 = { id: 2, buyer_id: 1, status: "active", created_at: "x", updated_at: "x" };
  const CONV_1 = { id: 1, buyer_id: 1, status: "closed", created_at: "x", updated_at: "x" };

  it("loads history from every conversation, merged chronologically", async () => {
    vi.mocked(getConversations).mockResolvedValue({
      conversations: [CONV_2, CONV_1],
    });
    vi.mocked(getMessages).mockImplementation(async (_client, id: number) => {
      if (id === 1) {
        return { messages: [makeMsg(1, 1, "最早的历史", "2026-08-10T00:00:00Z")] };
      }
      return { messages: [makeMsg(3, 2, "最近的内容", "2026-08-12T00:00:00Z")] };
    });

    const { result } = renderHook(() => useSSEChat());

    await vi.waitFor(() => {
      expect(result.current.messages.map((m) => m.content)).toEqual([
        "最早的历史",
        "最近的内容",
      ]);
    });

    expect(getMessages).toHaveBeenCalledTimes(2);
  });

  it("commits new messages to the latest conversation after streaming", async () => {
    vi.mocked(getConversations).mockResolvedValue({
      conversations: [CONV_2],
    });
    vi.mocked(getMessages).mockResolvedValue({
      messages: [makeMsg(3, 2, "旧内容")],
    });

    const { result } = renderHook(() => useSSEChat());
    const worker = workers[0];

    await vi.waitFor(() => {
      expect(result.current.messages.length).toBe(1);
    });

    act(() => {
      result.current.sendMessage("新消息");
    });

    emit(worker, { type: "status", content: "正在查找中", conversation_id: 2 });
    emit(worker, { type: "token", content: "回复" });
    emit(worker, { type: "done" });

    expect(
      result.current.messages.map((m) => m.content),
    ).toEqual(["旧内容", "新消息", "回复"]);
  });
});

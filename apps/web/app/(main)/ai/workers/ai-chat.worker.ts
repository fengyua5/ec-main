export {};

const worker = self as unknown as {
  onmessage: ((e: MessageEvent) => void) | null;
  postMessage: (data: unknown) => void;
};

type WorkerRequest = {
  url: string;
  payload: { conversation_id?: number | null; content: string };
};

async function parseSSE(response: Response): Promise<void> {
  const reader = response.body!.getReader();
  const decoder = new TextDecoder();
  let buffer = "";

  while (true) {
    const { done, value } = await reader.read();
    if (done) break;

    buffer += decoder.decode(value, { stream: true });
    const lines = buffer.split("\n");
    buffer = lines.pop() || "";

    for (const line of lines) {
      if (line.startsWith("data: ")) {
        const data = line.slice(6);
        try {
          worker.postMessage(JSON.parse(data));
        } catch {
          // skip malformed JSON
        }
      }
    }
  }
}

worker.onmessage = async (e: MessageEvent<WorkerRequest>) => {
  const { url, payload } = e.data;
  try {
    const response = await fetch(url, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      credentials: "include",
      body: JSON.stringify(payload),
    });

    if (!response.ok || !response.body) {
      worker.postMessage({ type: "error", content: "Chat request failed" });
      return;
    }

    await parseSSE(response);
  } catch {
    worker.postMessage({ type: "error", content: "Chat request failed" });
  }
};

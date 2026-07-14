import asyncio

from langchain_core.callbacks import BaseCallbackHandler


class SSECallbackHandler(BaseCallbackHandler):
    def __init__(self, queue: asyncio.Queue):
        self.queue = queue

    def on_llm_new_token(self, token: str, **kwargs):
        self.queue.put_nowait({"type": "token", "content": token})

    def on_llm_end(self, response, **kwargs) -> None:
        self.queue.put_nowait({"type": "done"})

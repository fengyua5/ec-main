import asyncio
import json
import logging
from collections.abc import AsyncGenerator


logger = logging.getLogger(__name__)


class MCPClient:
    """MCP Client 单例，管理 stdio 子进程生命周期。Task 4 实现完整逻辑。"""

    _instance: "MCPClient | None" = None

    def __init__(self) -> None:
        self._process: asyncio.subprocess.Process | None = None

    @classmethod
    def get_instance(cls) -> "MCPClient":
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    async def check_order(self, order_id: str) -> dict:
        raise NotImplementedError("Task 4 实现")

    async def process_refund(self, order_id: str, reason: str, amount: str) -> dict:
        raise NotImplementedError("Task 4 实现")

    async def close(self) -> None:
        pass

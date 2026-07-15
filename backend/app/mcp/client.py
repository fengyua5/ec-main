import asyncio
import json
import logging
from collections.abc import AsyncGenerator

logger = logging.getLogger(__name__)


class MCPClient:
    """MCP Client 单例，通过 stdio 子进程与 MCP Server 通信。"""

    _instance: "MCPClient | None" = None
    _request_id: int = 0

    def __init__(self) -> None:
        self._process: asyncio.subprocess.Process | None = None
        self._lock = asyncio.Lock()
        self._initialized: bool = False

    @classmethod
    def get_instance(cls) -> "MCPClient":
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    async def _ensure_process(self) -> None:
        if self._process is not None and self._process.returncode is None:
            return
        self._process = await asyncio.create_subprocess_exec(
            "uv",
            "run",
            "-m", "app.mcp",
            stdin=asyncio.subprocess.PIPE,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )

    async def _init_session(self) -> None:
        assert self._process is not None
        assert self._process.stdin is not None
        assert self._process.stdout is not None

        init_request = {
            "jsonrpc": "2.0",
            "id": 0,
            "method": "initialize",
            "params": {
                "protocolVersion": "2024-11-05",
                "capabilities": {},
                "clientInfo": {
                    "name": "ec-main",
                    "version": "1.0.0",
                },
            },
        }
        self._process.stdin.write(
            (json.dumps(init_request, ensure_ascii=False) + "\n").encode("utf-8"),
        )
        await self._process.stdin.drain()
        response = await self._process.stdout.readline()
        logger.debug("MCP 初始化响应: %s", response.decode("utf-8").strip())

        notif = {
            "jsonrpc": "2.0",
            "method": "notifications/initialized",
        }
        self._process.stdin.write(
            (json.dumps(notif, ensure_ascii=False) + "\n").encode("utf-8"),
        )
        await self._process.stdin.drain()
        self._initialized = True
        logger.info("MCP Client: 子进程已启动并完成初始化")

    async def _send_request(self, method: str, params: dict | None = None) -> dict:
        await self._ensure_process()
        if not self._initialized:
            await self._init_session()
        async with self._lock:
            MCPClient._request_id += 1
            req_id = MCPClient._request_id
            request = {
                "jsonrpc": "2.0",
                "id": req_id,
                "method": method,
                "params": params or {},
            }
            request_json = json.dumps(request, ensure_ascii=False) + "\n"
            assert self._process is not None
            assert self._process.stdin is not None
            self._process.stdin.write(request_json.encode("utf-8"))
            await self._process.stdin.drain()
            assert self._process.stdout is not None
            response = await self._process.stdout.readline()
            result = json.loads(response.decode("utf-8"))
            if "error" in result:
                raise RuntimeError(f"MCP error: {result['error']}")
            return result.get("result", {})

    async def check_order(self, order_id: str) -> dict:
        result = await self._send_request("tools/call", {
            "name": "check_order",
            "arguments": {"order_id": order_id},
        })
        content = result.get("content", [{}])[0].get("text", "{}")
        return json.loads(content)

    async def process_refund(self, order_id: str, reason: str, amount: str) -> dict:
        result = await self._send_request("tools/call", {
            "name": "process_refund",
            "arguments": {
                "order_id": order_id,
                "reason": reason,
                "amount": amount,
            },
        })
        content = result.get("content", [{}])[0].get("text", "{}")
        return json.loads(content)

    async def close(self) -> None:
        if self._process is not None and self._process.returncode is None:
            self._process.terminate()
            try:
                await asyncio.wait_for(self._process.wait(), timeout=5)
            except asyncio.TimeoutError:
                self._process.kill()
                await self._process.wait()
            logger.info("MCP Client: 子进程已终止")
            self._process = None
            self._initialized = False

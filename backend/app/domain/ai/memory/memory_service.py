import json
import logging
from dataclasses import dataclass

from langchain_core.messages import AIMessage, BaseMessage, HumanMessage
from sqlalchemy.orm import Session

from app.core.config import settings
from app.domain.ai.llm.chat import get_chat_llm
from app.domain.ai.memory.memory_repo import get_by_buyer, upsert
from app.domain.ai.memory.prompts import memory_update_prompt, MEMORY_INJECT_PREFIX

logger = logging.getLogger(__name__)


@dataclass
class MemoryUpdateResult:
    changed: bool
    content: str | None
    error: str | None


def _format_conversation(messages: list[BaseMessage]) -> str:
    lines = []
    for m in messages:
        if isinstance(m, HumanMessage):
            lines.append(f"用户: {m.content}")
        elif isinstance(m, AIMessage):
            lines.append(f"客服: {m.content}")
    return "\n".join(lines)


async def update_memory(
    db: Session,
    buyer_id: int,
    conversation_messages: list[BaseMessage],
) -> MemoryUpdateResult:
    existing = get_by_buyer(db, buyer_id)
    old_memory = existing.content if existing else ""
    expected_version = existing.version if existing else 0

    conversation_text = _format_conversation(conversation_messages)

    try:
        llm = get_chat_llm(temperature=0, streaming=False)
        chain = memory_update_prompt | llm
        response = await chain.ainvoke({
            "old_memory": old_memory or "（暂无）",
            "conversation": conversation_text,
        })
        raw = response.content.strip()
        if raw.startswith("```"):
            raw = raw.split("\n", 1)[-1].rsplit("```", 1)[0].strip()

        data = json.loads(raw)
        if not data.get("changed"):
            return MemoryUpdateResult(changed=False, content=None, error=None)

        new_content = data.get("content", "").strip()
        if not new_content:
            return MemoryUpdateResult(changed=False, content=None, error=None)

        ok = upsert(db, buyer_id, new_content, expected_version)
        if not ok:
            logger.warning("记忆更新乐观锁冲突，buyer_id=%d，本次跳过", buyer_id)
            return MemoryUpdateResult(changed=False, content=None, error="version conflict")

        return MemoryUpdateResult(changed=True, content=new_content, error=None)

    except Exception as e:
        logger.warning("记忆更新失败: %s", e)
        return MemoryUpdateResult(changed=False, content=None, error=str(e))


async def get_memory_block(db: Session, buyer_id: int) -> str | None:
    existing = get_by_buyer(db, buyer_id)
    if not existing or not existing.content:
        return None
    from app.domain.ai.workflow.compaction import estimate_tokens
    tokens = estimate_tokens(existing.content)
    if tokens <= settings.ai_memory_budget_tokens:
        return MEMORY_INJECT_PREFIX + existing.content
    chars = existing.content
    while chars and estimate_tokens(chars) > settings.ai_memory_budget_tokens:
        chars = chars[:-1]
    return MEMORY_INJECT_PREFIX + chars.strip() + "..."

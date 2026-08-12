"""对话历史上下文剪裁。

参考 pi-coding-agent（OpenClaw）的上下文压缩策略实现：
- Token 启发式估算 + 安全系数（SAFETY_MARGIN），补偿对中文等多字节字符的低估
- 历史预算 = 上下文窗口 - 预留（system prompt / FAQ / 输出）
- 保留最近消息（keepRecentTokens）原样不动，超预算部分交给 LLM 分段摘要
- 摘要失败兜底：回退为启发式截断，保证永远不因剪裁丢最近消息
"""

import logging
from collections.abc import Sequence
from dataclasses import dataclass

from langchain_core.messages import AIMessage, BaseMessage, HumanMessage, SystemMessage

from app.core.config import settings
from app.domain.ai.llm.chat import get_chat_llm
from app.domain.ai.llm.prompts import history_summary_prompt

logger = logging.getLogger(__name__)

SAFETY_MARGIN = 1.2
_MAX_FALLBACK_OLD_CHARS = 200
_FALLBACK_RESERVED_CHARS = 1500


@dataclass
class TrimResult:
    messages: list[BaseMessage]
    trimmed: bool
    old_count: int
    kept_count: int
    summary: str | None
    total_tokens: int
    budget_tokens: int


def estimate_tokens(text: str) -> int:
    """粗略估算 token 数：ASCII 约 4 字符/token，中文等非 ASCII 约 1 token/字符，乘安全系数。"""
    if not text:
        return 0
    ascii_chars = sum(1 for ch in text if ord(ch) < 128)
    non_ascii = len(text) - ascii_chars
    raw = ascii_chars / 4.0 + non_ascii * 1.1
    return max(1, int(raw * SAFETY_MARGIN))


def _history_budget() -> int:
    return max(256, settings.ai_context_window_tokens - settings.ai_history_reserved_tokens)


def _recent_budget() -> int:
    return settings.ai_history_keep_recent_tokens


def _group_into_turns(messages: Sequence[BaseMessage]) -> list[list[BaseMessage]]:
    """把消息按轮次分组：一个用户输入及其后续客服回复算作一轮，避免切分时拆散配对。"""
    turns: list[list[BaseMessage]] = []
    current: list[BaseMessage] = []
    for m in messages:
        if isinstance(m, HumanMessage) and current:
            turns.append(current)
            current = []
        current.append(m)
    if current:
        turns.append(current)
    return turns


def _split_by_tokens(messages: Sequence[BaseMessage], chunk_tokens: int) -> list[list[BaseMessage]]:
    chunks: list[list[BaseMessage]] = []
    current: list[BaseMessage] = []
    acc = 0
    for turn in _group_into_turns(messages):
        t = sum(estimate_tokens(m.content) for m in turn)
        if current and acc + t > chunk_tokens:
            chunks.append(current)
            current = []
            acc = 0
        current.extend(turn)
        acc += t
    if current:
        chunks.append(current)
    return chunks


def _format_history(messages: Sequence[BaseMessage]) -> str:
    lines = []
    for m in messages:
        if isinstance(m, HumanMessage):
            lines.append(f"用户: {m.content}")
        elif isinstance(m, AIMessage):
            lines.append(f"客服: {m.content}")
    return "\n".join(lines)


async def summarize_history(messages: Sequence[BaseMessage], chunk_tokens: int) -> str:
    """对旧消息做分段摘要（staged summarization），多段时再合并。"""
    llm = get_chat_llm(temperature=0, streaming=False)
    chain = history_summary_prompt | llm

    summaries: list[str] = []
    for chunk in _split_by_tokens(messages, chunk_tokens):
        text = _format_history(chunk)
        if not text:
            continue
        response = await chain.ainvoke({"history": text})
        content = response.content.strip()
        if content:
            summaries.append(content)

    if not summaries:
        return ""

    if len(summaries) == 1:
        return summaries[0]

    merged = "\n".join(f"[片段 {i + 1}]\n{s}" for i, s in enumerate(summaries))
    response = await chain.ainvoke({"history": merged})
    return response.content.strip() or " ".join(summaries)


def _fallback_compact(messages: Sequence[BaseMessage], budget_tokens: int) -> str:
    """LLM 摘要失败时的启发式兜底：保留每条旧消息开头，整体压缩到预算内。"""
    parts: list[str] = []
    used = 0
    for m in messages:
        content = m.content
        if isinstance(m, HumanMessage):
            prefix = "用户: "
        else:
            prefix = "客服: "
        snippet = content[:_MAX_FALLBACK_OLD_CHARS].strip()
        if not snippet:
            continue
        line = prefix + snippet
        parts.append(line)
        used += len(line) + len(prefix)
        if used >= _FALLBACK_RESERVED_CHARS:
            break
    if not parts:
        return "(早期对话已省略)"
    return "\n".join(parts)


async def trim_history(
    history: Sequence[BaseMessage],
    *,
    budget_tokens: int | None = None,
    keep_recent_tokens: int | None = None,
) -> TrimResult:
    """按预算剪裁历史：保留最近消息 + 旧消息 LLM 摘要。

    history 需按时间升序（最旧在前）。返回的新消息列表最前为摘要（若有），
    随后是完整保留的最近消息；当前用户消息不在 history 中，由调用方追加。
    """
    budget = budget_tokens if budget_tokens is not None else _history_budget()
    recent = keep_recent_tokens if keep_recent_tokens is not None else _recent_budget()

    total = sum(estimate_tokens(m.content) for m in history)
    if total <= budget or not history:
        return TrimResult(
            messages=list(history),
            trimmed=False,
            old_count=0,
            kept_count=len(history),
            summary=None,
            total_tokens=total,
            budget_tokens=budget,
        )

    kept: list[BaseMessage] = []
    acc = 0
    for turn in reversed(_group_into_turns(history)):
        turn_tokens = sum(estimate_tokens(m.content) for m in turn)
        kept = list(turn) + kept
        acc += turn_tokens
        if acc >= recent:
            break
    old = history[: len(history) - len(kept)]

    summary = None
    try:
        summary = await summarize_history(old, chunk_tokens=max(128, budget // 2))
    except Exception as e:
        logger.warning("历史摘要生成失败，回退启发式截断: %s", e)

    if summary:
        prefix = f"[历史对话摘要]\n{summary}"
    else:
        prefix = f"[早期对话已省略]\n{_fallback_compact(old, budget)}"

    result = ([SystemMessage(content=prefix)] if prefix else []) + kept

    return TrimResult(
        messages=result,
        trimmed=True,
        old_count=len(old),
        kept_count=len(kept),
        summary=summary,
        total_tokens=total,
        budget_tokens=budget,
    )
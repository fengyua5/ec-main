import pytest
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage

from app.domain.ai.workflow.compaction import (
    estimate_tokens,
    _fallback_compact,
    _group_into_turns,
    _split_by_tokens,
    summarize_history,
    trim_history,
)


def _ut(text: str):
    return estimate_tokens(text)


class TestEstimateTokens:
    def test_empty(self) -> None:
        assert _ut("") == 0

    def test_ascii(self) -> None:
        assert _ut("a" * 8) >= 1

    def test_cjk_counts_more(self) -> None:
        assert _ut("中文" * 100) > _ut("a" * 100)


class TestSplitByTokens:
    def test_split_respects_budget(self) -> None:
        msgs = [HumanMessage(content="你好" * 50) for _ in range(5)]
        chunks = _split_by_tokens(msgs, chunk_tokens=100)
        assert len(chunks) >= 2
        assert all(len(c) >= 1 for c in chunks)
        assert sum(len(c) for c in chunks) == len(msgs)

    def test_single_chunk_when_small(self) -> None:
        msgs = [HumanMessage(content="hi"), AIMessage(content="hello")]
        chunks = _split_by_tokens(msgs, chunk_tokens=1000)
        assert len(chunks) == 1


class TestGroupIntoTurns:
    def test_groups_user_ai_pairs(self) -> None:
        msgs = [
            HumanMessage(content="u1"),
            AIMessage(content="a1"),
            HumanMessage(content="u2"),
            AIMessage(content="a2"),
        ]
        turns = _group_into_turns(msgs)
        assert len(turns) == 2
        assert turns[0] == msgs[:2]
        assert turns[1] == msgs[2:]

    def test_lone_user_input_is_own_turn(self) -> None:
        msgs = [HumanMessage(content="u1"), AIMessage(content="a1"), HumanMessage(content="u2")]
        turns = _group_into_turns(msgs)
        assert len(turns) == 2
        assert turns[0] == msgs[:2]
        assert turns[1] == [msgs[2]]

    def test_split_never_splits_a_turn(self) -> None:
        msgs = [
            HumanMessage(content="u1"),
            AIMessage(content="a1"),
            HumanMessage(content="u2"),
            AIMessage(content="a2"),
        ]
        chunks = _split_by_tokens(msgs, chunk_tokens=1)
        for chunk in chunks:
            contents = [m.content for m in chunk]
            assert contents not in (["u1"], ["a1"])
            assert contents not in (["u2"], ["a2"])


class TestFallbackCompact:
    def test_truncates_and_limits(self) -> None:
        msgs = [HumanMessage(content="长内容" * 500) for _ in range(50)]
        text = _fallback_compact(msgs, budget_tokens=100)
        assert "长内容" in text
        assert len(text) <= 2000

    def test_empty(self) -> None:
        assert _fallback_compact([], budget_tokens=100) == "(早期对话已省略)"


class TestSummarizeHistory:
    @pytest.mark.asyncio
    async def test_single_chunk_summary(self) -> None:
        from unittest.mock import AsyncMock, MagicMock, patch

        with patch("app.domain.ai.workflow.compaction.get_chat_llm") as mock_llm_cls, \
             patch("app.domain.ai.workflow.compaction.history_summary_prompt") as mock_prompt:
            mock_chain = AsyncMock()
            mock_chain.ainvoke.return_value = MagicMock(content="订单 ORD-1 退款待处理")
            mock_prompt.__or__.return_value = mock_chain

            msgs = [HumanMessage(content="我想退款"), AIMessage(content="请提供订单号")]
            res = await summarize_history(msgs, chunk_tokens=1000)
            assert res == "订单 ORD-1 退款待处理"

    @pytest.mark.asyncio
    async def test_empty_history(self) -> None:
        res = await summarize_history([], chunk_tokens=100)
        assert res == ""


class TestTrimHistory:
    @pytest.mark.asyncio
    async def test_within_budget_no_trim(self) -> None:
        msgs = [HumanMessage(content="你好"), AIMessage(content="你好！有什么可以帮您？")]
        result = await trim_history(msgs, budget_tokens=1000, keep_recent_tokens=500)
        assert result.trimmed is False
        assert result.messages == msgs
        assert result.kept_count == 2

    @pytest.mark.asyncio
    async def test_keeps_recent_and_summarizes_old(self) -> None:
        from unittest.mock import AsyncMock, MagicMock, patch

        with patch("app.domain.ai.workflow.compaction.get_chat_llm") as mock_llm_cls, \
             patch("app.domain.ai.workflow.compaction.history_summary_prompt") as mock_prompt:
            mock_chain = AsyncMock()
            mock_chain.ainvoke.return_value = MagicMock(content="早期退款诉求：退款 ORD-1")
            mock_prompt.__or__.return_value = mock_chain

            old = [HumanMessage(content="我要退款" * 20) for _ in range(10)]
            recent = [HumanMessage(content="后退货政策"), AIMessage(content="30 天内可退")]
            history = old + recent

            result = await trim_history(history, budget_tokens=30, keep_recent_tokens=10)

            assert result.trimmed is True
            assert result.old_count >= 1
            assert result.kept_count >= 1
            assert isinstance(result.messages[0], SystemMessage)
            assert "早期退款诉求" in result.messages[0].content
            recent_contents = [getattr(m, "content", "") for m in result.messages[1:]]
            assert recent_contents == [m.content for m in recent]

    @pytest.mark.asyncio
    async def test_fallback_on_llm_failure(self) -> None:
        from unittest.mock import AsyncMock, MagicMock, patch

        with patch("app.domain.ai.workflow.compaction.get_chat_llm") as mock_llm_cls, \
             patch("app.domain.ai.workflow.compaction.history_summary_prompt") as mock_prompt:
            mock_chain = AsyncMock()
            mock_chain.ainvoke.side_effect = RuntimeError("ollama down")
            mock_prompt.__or__.return_value = mock_chain

            old = [HumanMessage(content="我要退款" * 20) for _ in range(10)]
            recent = [HumanMessage(content="后退货政策")]
            history = old + recent

            result = await trim_history(history, budget_tokens=100, keep_recent_tokens=50)

            assert result.trimmed is True
            assert result.summary is None
            assert isinstance(result.messages[0], SystemMessage)
            assert "[早期对话已省略]" in result.messages[0].content
            assert result.messages[-1].content == "后退货政策"

    @pytest.mark.asyncio
    async def test_empty_history(self) -> None:
        result = await trim_history([], budget_tokens=100)
        assert result.trimmed is False
        assert result.messages == []
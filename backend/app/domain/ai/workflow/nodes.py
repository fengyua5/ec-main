import json
import logging

from langchain_core.messages import HumanMessage

from app.domain.ai.llm.chat import get_chat_llm
from app.domain.ai.llm.prompts import (
    GREETING_RESPONSE,
    intent_prompt,
    faq_prompt,
)
from app.domain.ai.rag import FaqIndexService, FaqRetriever
from app.mcp.client import MCPClient
from app.domain.ai.models.conversation_repo import ConversationRepository
from app.domain.ai.workflow.state import ConversationState

logger = logging.getLogger(__name__)


async def classify_intent(state: ConversationState) -> dict:
    last_user_msg = None
    last_ai_msg = None
    for m in reversed(state["messages"]):
        if isinstance(m, HumanMessage):
            if last_user_msg is None:
                last_user_msg = m.content
        else:
            if last_ai_msg is None:
                last_ai_msg = m.content
        if last_user_msg is not None and last_ai_msg is not None:
            break

    if not last_user_msg:
        logger.info("意图识别: 无用户消息，默认转人工")
        return {"flow": {"intent": "human", "confidence": 0.0}}

    context_parts = []
    if last_ai_msg:
        context_parts.append(f"上一条回复: {last_ai_msg}")
    context_parts.append(f"用户: {last_user_msg}")

    llm = get_chat_llm(temperature=0, streaming=False)
    chain = intent_prompt | llm
    response = await chain.ainvoke({"user_input": "\n".join(context_parts)})
    print("意图返回", response.content);
    try:
        result = json.loads(response.content.strip())
        intent = result.get("intent", "human")
        confidence = float(result.get("confidence", 0.0))
        if confidence < 0.5:
            logger.info("意图识别: 置信度 %.2f < 0.5，降级转人工", confidence)
            intent = "human"
        else:
            logger.info("意图识别: %s (置信度 %.2f)", intent, confidence)
    except (json.JSONDecodeError, ValueError, AttributeError) as e:
        logger.warning("意图识别: LLM 返回解析失败: %s", e)
        intent = "human"
        confidence = 0.0

    return {"flow": {"intent": intent, "confidence": confidence}}


async def handle_greeting(state: ConversationState) -> dict:
    logger.info("问候处理: 返回欢迎语")
    return {"flow": {"response": GREETING_RESPONSE}}


async def retrieve_faq(state: ConversationState) -> dict:
    last_user_msg = None
    for m in reversed(state["messages"]):
        if isinstance(m, HumanMessage):
            last_user_msg = m.content
            break

    if not last_user_msg:
        logger.info("FAQ 检索: 无用户消息")
        return {"skills": {"faq": {"context": []}}, "flow": {"intent": "human"}}

    retriever = FaqRetriever(FaqIndexService())
    results = retriever.retrieve(last_user_msg)

    logger.info("FAQ 检索: query='%s' 命中 %d 条", last_user_msg[:50], len(results))
    if not results:
        return {"skills": {"faq": {"context": []}}, "flow": {"intent": "human"}}

    return {"skills": {"faq": {"context": results}}}


async def answer_faq(state: ConversationState) -> dict:
    faq_context = state.get("skills", {}).get("faq", {}).get("context", [])
    last_user_msg = None
    for m in reversed(state["messages"]):
        if isinstance(m, HumanMessage):
            last_user_msg = m.content
            break

    if not last_user_msg or not faq_context:
        logger.info("FAQ 回答: 缺少上下文或问题，返回兜底")
        return {"flow": {"response": "抱歉，无法找到相关的 FAQ 信息。"}}

    context_text = "\n\n".join(c["content"] for c in faq_context)

    llm = get_chat_llm(temperature=0, streaming=False)
    chain = faq_prompt | llm
    response = await chain.ainvoke({"context": context_text, "question": last_user_msg})

    logger.info("FAQ 回答: 生成回复（长度 %d 字符）", len(response.content))
    return {"flow": {"response": response.content}}


async def collect_refund_info(state: ConversationState) -> dict:
    refund_info = dict(state.get("skills", {}).get("refund", {}))
    messages = state["messages"]
    last_msg = messages[-1].content if messages else ""

    if "order_no" not in refund_info:
        refund_info["order_no"] = last_msg
        logger.info("退单收集: 已记录订单号 '%s'", last_msg[:30])
        return {"flow": {"response": "请输入退款原因："}, "skills": {"refund": refund_info}}

    if "reason" not in refund_info:
        refund_info["reason"] = last_msg
        logger.info("退单收集: 已记录退款原因 '%s'", last_msg[:30])
        return {"flow": {"response": "请输入退款金额："}, "skills": {"refund": refund_info}}

    if "amount" not in refund_info:
        refund_info["amount"] = last_msg
        logger.info("退单收集: 已记录退款金额 '%s'", last_msg[:30])
        return {"skills": {"refund": refund_info}}

    logger.info("退单收集: 信息已完整，准备提交流程")
    return {"skills": {"refund": refund_info}}


async def process_refund(state: ConversationState) -> dict:
    refund_info = state.get("skills", {}).get("refund", {})
    logger.info(
        "退单处理: 订单号=%s, 原因=%s, 金额=%s",
        refund_info.get("order_no", "?"),
        refund_info.get("reason", "?"),
        refund_info.get("amount", "?"),
    )
    return {"flow": {"response": "退单申请已提交，处理成功！"}}


async def handoff_human(state: ConversationState) -> dict:
    conv_id = state.get("flow", {}).get("conversation_id")
    if conv_id is not None:
        repo = ConversationRepository()
        try:
            from app.db.session import SessionLocal
            db = SessionLocal()
            try:
                repo.update_status(db, conv_id, "waiting_human")
                logger.info("转人工: 会话 %d 状态已更新为 waiting_human", conv_id)
            finally:
                db.close()
        except Exception as e:
            logger.error("转人工: 更新会话 %d 状态失败: %s", conv_id, e)
    logger.info("转人工: 会话 %d 正在转接", conv_id)
    return {"flow": {"response": "正在为您转接人工客服，请稍候..."}}


async def check_order_mcp(state: ConversationState) -> dict:
    refund_info = state.get("skills", {}).get("refund", {})
    order_id = refund_info.get("order_no", "")
    if not order_id:
        return {"mcp": {"order_status": "not_found", "error": "缺少订单号"}, "flow": {"response": "未提供订单号，请重新输入。"}}

    client = MCPClient.get_instance()
    try:
        result = await client.check_order(order_id)
        status = result.get("status", "not_found")
        logger.info("MCP check_order: order=%s status=%s", order_id, status)

        if status == "pending_delivery":
            return {"mcp": {"order_status": status}}
        elif status == "in_delivery":
            return {"mcp": {"order_status": status}, "flow": {"response": "您的订单正在配送中，暂时无法退款。"}}
        elif status == "delivered":
            return {"mcp": {"order_status": status}, "flow": {"response": "订单已签收，请通过售后渠道申请退款。"}}
        else:
            return {"mcp": {"order_status": "not_found"}, "flow": {"response": f"未找到订单 {order_id}，请确认订单号是否正确。"}}
    except Exception as e:
        logger.error("MCP check_order 异常: %s", e)
        return {"mcp": {"order_status": "error", "error": str(e)}, "flow": {"intent": "human"}}


async def process_refund_mcp(state: ConversationState) -> dict:
    refund_info = state.get("skills", {}).get("refund", {})
    order_id = refund_info.get("order_no", "")
    reason = refund_info.get("reason", "")
    amount = refund_info.get("amount", "")

    client = MCPClient.get_instance()
    try:
        result = await client.process_refund(order_id, reason, amount)
        if result.get("success"):
            logger.info("MCP process_refund: order=%s 退款成功", order_id)
            return {"mcp": {"refund_success": True}, "flow": {"response": f"退款成功！订单 {order_id} 已退款 {amount} 元。（原因：{reason}）"}}
        else:
            logger.warning("MCP process_refund: order=%s 退款失败: %s", order_id, result.get("message", ""))
            return {"mcp": {"refund_success": False}, "flow": {"response": f"退款失败：{result.get('message', '未知错误')}"}}
    except Exception as e:
        logger.error("MCP process_refund 异常: %s", e)
        return {"mcp": {"refund_success": False, "error": str(e)}, "flow": {"intent": "human"}}

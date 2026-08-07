import json
import logging
import re

from langchain_core.messages import HumanMessage

from app.db.session import SessionLocal
from app.domain.after_sale import create_case
from app.domain.ai.llm.chat import get_chat_llm
from app.domain.ai.llm.prompts import (
    GREETING_RESPONSE,
    intent_prompt,
    sub_intent_prompt,
    faq_prompt,
)
from app.domain.ai.rag import FaqIndexService, FaqRetriever
from app.mcp.client import MCPClient
from app.domain.ai.models.conversation_repo import ConversationRepository
from app.domain.ai.workflow.state import ConversationState

logger = logging.getLogger(__name__)

_ORDER_STATUS_LABELS = {
    "pending_payment": "待付款",
    "pending_delivery": "待发货",
    "in_delivery": "配送中",
    "delivered": "已送达",
    "cancelled": "已取消",
    "refunded": "已退款",
}

_SUB_INTENT_LABELS = {
    "refund": "退款",
    "cancel_order": "取消订单",
    "update_order": "修改订单",
    "query_order": "查询订单",
}


def _merge_skills(state: ConversationState, **updates: dict) -> dict:
    skills = dict(state.get("skills", {}))
    skills.update(updates)
    return skills


async def classify_intent(state: ConversationState) -> dict:
    refund = state.get("skills", {}).get("refund", {})
    has_refund_info = bool(refund) and not all(k in refund for k in ("order_no", "reason", "amount"))
    if has_refund_info:
        logger.info("意图识别: 退单流程进行中，跳过 LLM 分类，返回 refund")
        return {"flow": {"intent": "after_sale", "sub_intent": "refund", "confidence": 1.0}}

    after_sale = state.get("skills", {}).get("after_sale", {})
    if after_sale.get("sub_intent"):
        logger.info("意图识别: 售后流程进行中，跳过 LLM 分类，返回 after_sale")
        return {"flow": {"intent": "after_sale", "sub_intent": after_sale.get("sub_intent"), "confidence": 1.0}}

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
        return {"flow": {"response": "抱歉，暂时没有找到相关的 FAQ 信息，正在为您转接人工客服，请稍候。"}}

    context_parts = []
    for c in faq_context:
        content = c["content"]
        source = c.get("source", "")
        if source:
            context_parts.append(f"[来源: {source}]\n{content}")
        else:
            context_parts.append(content)
    context_text = "\n\n".join(context_parts)

    llm = get_chat_llm(temperature=0, streaming=False)
    chain = faq_prompt | llm
    response = await chain.ainvoke({"context": context_text, "question": last_user_msg})

    logger.info("FAQ 回答: 生成回复（长度 %d 字符）", len(response.content))
    return {"flow": {"response": response.content}}


async def collect_refund_info(state: ConversationState) -> dict:
    after_sale = dict(state.get("skills", {}).get("after_sale", {}))
    order_no = after_sale.get("order_no", "")
    refund_info = dict(state.get("skills", {}).get("refund", {}))
    if order_no:
        refund_info["order_no"] = order_no
    messages = state["messages"]
    last_msg = messages[-1].content if messages else ""

    if "reason" not in refund_info:
        refund_info["reason"] = last_msg
        logger.info("退单收集: 已记录退款原因 '%s'", last_msg[:30])
        return {"flow": {"response": "请输入退款金额："}, "skills": _merge_skills(state, refund=refund_info, after_sale=after_sale)}

    if "amount" not in refund_info:
        refund_info["amount"] = last_msg
        logger.info("退单收集: 已记录退款金额 '%s'", last_msg[:30])
        return {"skills": _merge_skills(state, refund=refund_info, after_sale=after_sale)}

    logger.info("退单收集: 信息已完整，准备提交流程")
    return {"skills": _merge_skills(state, refund=refund_info, after_sale=after_sale)}


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
    after_sale = dict(state.get("skills", {}).get("after_sale", {}))
    sub_intent = after_sale.get("sub_intent", "refund")
    order_id = after_sale.get("order_no", "")
    if not order_id:
        return {"mcp": {"order_status": "not_found", "error": "缺少订单号"}, "flow": {"response": "未提供订单号，请重新输入。"}}

    client = MCPClient.get_instance()
    try:
        result = await client.check_order(order_id)
        status = result.get("status", "not_found")
        buyer_id = result.get("buyer_id", 0)
        logger.info("MCP check_order: order=%s status=%s", order_id, status)

        if status in ("pending_payment", "pending_delivery"):
            after_sale["order_buyer_id"] = buyer_id
            return {
                "mcp": {"order_status": status, "order_buyer_id": buyer_id},
                "skills": _merge_skills(state, after_sale=after_sale),
            }
        if status in ("in_delivery", "delivered"):
            if sub_intent == "refund":
                msg = "您的订单已发货/签收，暂时无法退款，请通过售后渠道处理。"
            elif status == "in_delivery":
                msg = "您的订单配送中，无法取消。"
            else:
                msg = "您的订单已签收，无法取消。"
            return {"mcp": {"order_status": status}, "flow": {"response": msg}}
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
            after_sale = dict(state.get("skills", {}).get("after_sale", {}))
            buyer_id = after_sale.get("order_buyer_id", 0) or state.get("mcp", {}).get("order_buyer_id", 0)
            try:
                db = SessionLocal()
                try:
                    create_case(db, order_no=order_id, buyer_id=buyer_id, case_type="refund", amount=amount, reason=reason)
                finally:
                    db.close()
            except Exception as case_e:
                logger.error("售后 case 落库失败: %s", case_e)
            after_sale.pop("sub_intent", None)
            after_sale.pop("order_no", None)
            after_sale.pop("confirmed", None)
            after_sale.pop("order_buyer_id", None)
            return {
                "mcp": {"refund_success": True},
                "flow": {"response": f"退款成功！订单 {order_id} 已退款 {amount} 元。（原因：{reason}）"},
                "skills": _merge_skills(state, after_sale=after_sale, refund={}),
            }
        else:
            logger.warning("MCP process_refund: order=%s 退款失败: %s", order_id, result.get("message", ""))
            return {"mcp": {"refund_success": False}, "flow": {"response": f"退款失败：{result.get('message', '未知错误')}"}}
    except Exception as e:
        logger.error("MCP process_refund 异常: %s", e)
        return {"mcp": {"refund_success": False, "error": str(e)}, "flow": {"intent": "human"}}


async def enter_after_sale(state: ConversationState) -> dict:
    after_sale = dict(state.get("skills", {}).get("after_sale", {}))
    sub_intent = state.get("flow", {}).get("sub_intent") or after_sale.get("sub_intent")

    if sub_intent:
        logger.info("售后入口: 子意图已确定 %s，跳过分类", sub_intent)
        after_sale["sub_intent"] = sub_intent
        return {"skills": _merge_skills(state, after_sale=after_sale)}

    last_user_msg = None
    for m in reversed(state["messages"]):
        if isinstance(m, HumanMessage):
            last_user_msg = m.content
            break

    if not last_user_msg:
        logger.info("售后入口: 无用户消息，默认 query_order")
        after_sale["sub_intent"] = "query_order"
        return {"skills": _merge_skills(state, after_sale=after_sale)}

    llm = get_chat_llm(temperature=0, streaming=False)
    chain = sub_intent_prompt | llm
    response = await chain.ainvoke({"user_input": last_user_msg})
    try:
        result = json.loads(response.content.strip())
        sub_intent = result.get("sub_intent", "query_order")
        confidence = float(result.get("confidence", 0.0))
        if confidence < 0.5:
            logger.info("售后子意图: 置信度 %.2f < 0.5，默认 query_order", confidence)
            sub_intent = "query_order"
        else:
            logger.info("售后子意图: %s (置信度 %.2f)", sub_intent, confidence)
    except (json.JSONDecodeError, ValueError, AttributeError) as e:
        logger.warning("售后子意图: LLM 返回解析失败: %s", e)
        sub_intent = "query_order"

    after_sale["sub_intent"] = sub_intent
    return {"skills": _merge_skills(state, after_sale=after_sale)}


_ORDER_NO_PATTERN = re.compile(r"ORD-[A-Za-z0-9-]+")


async def ensure_order_no(state: ConversationState) -> dict:
    after_sale = dict(state.get("skills", {}).get("after_sale", {}))
    if after_sale.get("order_no"):
        return {"skills": _merge_skills(state, after_sale=after_sale)}

    messages = state["messages"]
    last_msg = messages[-1].content if messages else ""
    match = _ORDER_NO_PATTERN.search(last_msg)
    if match:
        after_sale["order_no"] = match.group(0)
        logger.info("售后槽位: 识别到订单号 '%s'", match.group(0))
        return {"skills": _merge_skills(state, after_sale=after_sale)}
    logger.info("售后槽位: 未识别到订单号，询问用户")
    return {
        "flow": {"response": "请提供订单号（格式 ORD-xxx）："},
        "skills": _merge_skills(state, after_sale=after_sale),
    }


_YES_WORDS = {"是", "确认", "好的", "可以", "确定", "嗯", "对", "是的"}
_NO_WORDS = {"否", "不", "算了", "不要", "不要了", "不是", "不用"}


def _classify_confirm(text: str) -> str | None:
    stripped = text.strip().strip("？！。，,.").lower()
    if len(stripped) <= 4:
        if stripped in _YES_WORDS:
            return "yes"
        if stripped in _NO_WORDS:
            return "no"
    return None


async def confirm_after_sale(state: ConversationState) -> dict:
    after_sale = dict(state.get("skills", {}).get("after_sale", {}))
    refund = dict(state.get("skills", {}).get("refund", {}))
    sub_intent = after_sale.get("sub_intent", "")
    order_id = after_sale.get("order_no", "")
    messages = state["messages"]
    last_msg = messages[-1].content if messages else ""

    verdict = _classify_confirm(last_msg)
    if verdict == "yes":
        after_sale["confirmed"] = True
        after_sale.pop("confirmed_asked", None)
        logger.info("售后确认: 用户确认 %s 订单 %s", sub_intent, order_id)
        return {"skills": _merge_skills(state, after_sale=after_sale, refund=refund)}
    if verdict == "no":
        after_sale.pop("confirmed", None)
        after_sale.pop("order_no", None)
        after_sale.pop("sub_intent", None)
        after_sale.pop("order_buyer_id", None)
        logger.info("售后确认: 用户取消操作 %s", sub_intent)
        label = _SUB_INTENT_LABELS.get(sub_intent, sub_intent)
        return {
            "flow": {"response": f"已为您取消「{label}」操作。"},
            "skills": _merge_skills(state, after_sale=after_sale, refund={}),
        }

    if sub_intent == "refund":
        amount = refund.get("amount", "?")
        return {
            "flow": {"response": f"订单 {order_id} 金额 ¥{amount}，确认退款吗？（回复「确认」或「否」）"},
            "skills": _merge_skills(state, after_sale=after_sale, refund=refund),
        }
    return {
        "flow": {"response": f"确认取消订单 {order_id} 吗？（回复「确认」或「否」）"},
        "skills": _merge_skills(state, after_sale=after_sale, refund=refund),
    }


async def cancel_order_mcp(state: ConversationState) -> dict:
    after_sale = state.get("skills", {}).get("after_sale", {})
    order_id = after_sale.get("order_no", "")
    if not order_id:
        return {"mcp": {"cancel_success": False, "error": "缺少订单号"}, "flow": {"response": "缺少订单号，请重新输入。"}}

    client = MCPClient.get_instance()
    try:
        result = await client.update_order_status(order_id, "cancelled")
        if result.get("success"):
            logger.info("MCP cancel_order: order=%s 已取消", order_id)
            after_sale = dict(state.get("skills", {}).get("after_sale", {}))
            buyer_id = after_sale.get("order_buyer_id", 0) or state.get("mcp", {}).get("order_buyer_id", 0)
            try:
                db = SessionLocal()
                try:
                    create_case(db, order_no=order_id, buyer_id=buyer_id, case_type="cancel")
                finally:
                    db.close()
            except Exception as case_e:
                logger.error("售后 case 落库失败: %s", case_e)
            after_sale.pop("sub_intent", None)
            after_sale.pop("order_no", None)
            after_sale.pop("confirmed", None)
            after_sale.pop("order_buyer_id", None)
            return {
                "mcp": {"cancel_success": True},
                "flow": {"response": f"订单 {order_id} 已成功取消。"},
                "skills": _merge_skills(state, after_sale=after_sale),
            }
        else:
            logger.warning("MCP cancel_order: order=%s 取消失败: %s", order_id, result.get("message", ""))
            return {"mcp": {"cancel_success": False}, "flow": {"response": f"订单取消失败：{result.get('message', '未知错误')}"}}
    except Exception as e:
        logger.error("MCP cancel_order 异常: %s", e)
        return {"mcp": {"cancel_success": False, "error": str(e)}, "flow": {"intent": "human"}}


async def collect_order_no(state: ConversationState) -> dict:
    after_sale = dict(state.get("skills", {}).get("after_sale", {}))
    query_order = dict(after_sale.get("query_order", {}))
    order_no = after_sale.get("order_no", "")
    query_order["order_no"] = order_no
    after_sale["query_order"] = query_order
    logger.info("售后查询: 从统一槽位取订单号 '%s'", order_no)
    return {"skills": _merge_skills(state, after_sale=after_sale)}


async def query_order_mcp(state: ConversationState) -> dict:
    order_id = state.get("skills", {}).get("after_sale", {}).get("query_order", {}).get("order_no", "")
    if not order_id:
        return {"mcp": {"order_status": "not_found", "error": "缺少订单号"}, "flow": {"response": "未提供订单号，请重新输入。"}}

    client = MCPClient.get_instance()
    try:
        result = await client.check_order(order_id)
        status = result.get("status", "not_found")
        logger.info("MCP query_order: order=%s status=%s", order_id, status)

        if status == "not_found":
            return {"mcp": {"order_status": "not_found"}, "flow": {"response": f"未找到订单 {order_id}，请确认订单号是否正确。"}}
        if status == "error":
            return {"mcp": {"order_status": "error"}, "flow": {"response": "订单查询失败，请稍后重试或转人工客服。"}}

        status_label = _ORDER_STATUS_LABELS.get(status, status)
        return {
            "mcp": {"order_status": status},
            "flow": {
                "response": f"订单 {order_id} 查询成功：金额 ¥{result.get('amount', '?')}，状态 {status_label}，创建时间 {result.get('created_at', '?')}。"
            },
        }
    except Exception as e:
        logger.error("MCP query_order 异常: %s", e)
        return {"mcp": {"order_status": "error", "error": str(e)}, "flow": {"intent": "human"}}


async def collect_update_order_info(state: ConversationState) -> dict:
    after_sale = dict(state.get("skills", {}).get("after_sale", {}))
    update_order = dict(after_sale.get("update_order", {}))
    messages = state["messages"]
    last_msg = messages[-1].content if messages else ""
    order_no = after_sale.get("order_no", "")

    if "order_no" not in update_order:
        update_order["order_no"] = order_no
        after_sale["update_order"] = update_order
        logger.info("售后修改: 已记录订单号 '%s'", order_no)
        return {"flow": {"response": "已记录订单号，请告诉我您想修改为哪个状态（例如：待发货、配送中、已送达）："}, "skills": _merge_skills(state, after_sale=after_sale)}

    if "status" not in update_order:
        update_order["status"] = last_msg
        after_sale["update_order"] = update_order
        logger.info("售后修改: 已记录目标状态 '%s'", last_msg[:30])
        return {"skills": _merge_skills(state, after_sale=after_sale)}

    logger.info("售后修改: 信息已完整，准备提交修改")
    return {"skills": _merge_skills(state, after_sale=after_sale)}


async def update_order_mcp(state: ConversationState) -> dict:
    update_order = state.get("skills", {}).get("after_sale", {}).get("update_order", {})
    order_id = update_order.get("order_no", "")
    status = update_order.get("status", "")
    if not order_id or not status:
        return {"mcp": {"update_success": False, "error": "缺少订单信息"}, "flow": {"response": "缺少订单号或目标状态，请重新输入。"}}

    client = MCPClient.get_instance()
    try:
        result = await client.update_order_status(order_id, status)
        if result.get("success"):
            logger.info("MCP update_order: order=%s 修改为 %s", order_id, status)
            return {"mcp": {"update_success": True}, "flow": {"response": f"订单 {order_id} 已成功修改为「{status}」状态。"}}
        else:
            logger.warning("MCP update_order: order=%s 修改失败: %s", order_id, result.get("message", ""))
            return {"mcp": {"update_success": False}, "flow": {"response": f"订单修改失败：{result.get('message', '未知错误')}"}}
    except Exception as e:
        logger.error("MCP update_order 异常: %s", e)
        return {"mcp": {"update_success": False, "error": str(e)}, "flow": {"intent": "human"}}

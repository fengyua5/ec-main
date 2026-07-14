import json

from langchain_core.messages import HumanMessage

from app.domain.ai.llm.chat import get_chat_llm
from app.domain.ai.llm.prompts import (
    GREETING_RESPONSE,
    intent_prompt,
    faq_prompt,
)
from app.domain.ai.rag import FaqIndexService, FaqRetriever
from app.domain.ai.models.conversation_repo import ConversationRepository
from app.domain.ai.workflow.state import ConversationState


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
        return {"intent": "human", "confidence": 0.0}

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
            intent = "human"
    except (json.JSONDecodeError, ValueError, AttributeError):
        intent = "human"
        confidence = 0.0

    return {"intent": intent, "confidence": confidence}


async def handle_greeting(state: ConversationState) -> dict:
    return {"response": GREETING_RESPONSE}


async def retrieve_faq(state: ConversationState) -> dict:
    last_user_msg = None
    for m in reversed(state["messages"]):
        if isinstance(m, HumanMessage):
            last_user_msg = m.content
            break

    if not last_user_msg:
        return {"faq_context": [], "intent": "human"}

    retriever = FaqRetriever(FaqIndexService())
    results = retriever.retrieve(last_user_msg)

    if not results:
        return {"faq_context": [], "intent": "human"}

    return {"faq_context": results}


async def answer_faq(state: ConversationState) -> dict:
    faq_context = state.get("faq_context", [])
    last_user_msg = None
    for m in reversed(state["messages"]):
        if isinstance(m, HumanMessage):
            last_user_msg = m.content
            break

    if not last_user_msg or not faq_context:
        return {"response": "抱歉，无法找到相关的 FAQ 信息。"}

    context_text = "\n\n".join(c["content"] for c in faq_context)

    llm = get_chat_llm(temperature=0, streaming=False)
    chain = faq_prompt | llm
    response = await chain.ainvoke({"context": context_text, "question": last_user_msg})

    return {"response": response.content}


async def collect_refund_info(state: ConversationState) -> dict:
    refund_info = dict(state.get("refund_info", {}))
    messages = state["messages"]
    last_msg = messages[-1].content if messages else ""

    if "order_no" not in refund_info:
        refund_info["order_no"] = last_msg
        return {"response": "请输入退款原因：", "refund_info": refund_info}

    if "reason" not in refund_info:
        refund_info["reason"] = last_msg
        return {"response": "请输入退款金额：", "refund_info": refund_info}

    if "amount" not in refund_info:
        refund_info["amount"] = last_msg
        return {"refund_info": refund_info}

    return {"refund_info": refund_info}


async def process_refund(state: ConversationState) -> dict:
    return {"response": "退单申请已提交，处理成功！"}


async def handoff_human(state: ConversationState) -> dict:
    conv_id = state.get("conversation_id")
    if conv_id is not None:
        repo = ConversationRepository()
        try:
            from app.db.session import SessionLocal
            db = SessionLocal()
            try:
                repo.update_status(db, conv_id, "waiting_human")
            finally:
                db.close()
        except Exception:
            pass
    return {"response": "正在为您转接人工客服，请稍候..."}

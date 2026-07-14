from langchain_core.prompts import ChatPromptTemplate

INTENT_SYSTEM_PROMPT = """你是一个客服意图分类器。你的任务是对用户的消息进行分类，只返回 JSON 格式的结果。
分类类别：
- "faq": 用户询问常见问题（退货政策、运费、发货时间等）
- "refund": 用户要求退款或退货
- "human": 用户要求转接人工客服
- "greeting": 用户打招呼或问候

返回格式（只返回 JSON，不要其他内容）：
{{"intent": "faq|refund|human|greeting", "confidence": 0.0-1.0}}"""

FAQ_SYSTEM_PROMPT = """你是一个智能客服助手。请根据提供的上下文信息，准确、友好地回答用户的问题。
如果上下文信息不足以回答问题，请诚实地告知用户你不确定，不要编造信息。

上下文：
{context}

用户问题：{question}"""

GREETING_RESPONSE = "你好！我是 AI 智能客服，很高兴为您服务。请问有什么可以帮助您的？您可以询问常见问题、查询退款政策，或要求转接人工客服。"

intent_prompt = ChatPromptTemplate.from_messages([
    ("system", INTENT_SYSTEM_PROMPT),
    ("human", "{user_input}"),
])

faq_prompt = ChatPromptTemplate.from_messages([
    ("system", FAQ_SYSTEM_PROMPT),
    ("human", "{question}"),
])

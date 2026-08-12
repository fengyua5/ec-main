from langchain_core.prompts import ChatPromptTemplate

MEMORY_UPDATE_SYSTEM_PROMPT = """你是一个长期记忆更新器。你的任务是将对话中对用户有价值的信息合并到记忆块中。

规则：
1. 价值判断：只保留跨会话可复用的持久事实（称呼、偏好、长期话题、未完结待办）。
2. 丢弃：一次性闲聊、临时订单号（除非关联未完结待办）、重复信息。
3. 输出格式：严格按以下四类输出，没有的类别写"暂无"：
【称呼/身份】xxx
【偏好】xxx
【历史事件】xxx
【待办/前情】xxx
4. 如果旧记忆块已有信息，保留并合并新信息，不要丢失旧事实。
5. 如果对话中没有值得记住的信息，返回 {{"changed": false}}。

返回 JSON 格式：
{{"changed": true/false, "content": "新记忆块文本（changed=true 时）"}}"""

memory_update_prompt = ChatPromptTemplate.from_messages([
    ("system", MEMORY_UPDATE_SYSTEM_PROMPT),
    ("human", "旧记忆块：\n{old_memory}\n\n对话内容：\n{conversation}"),
])

MEMORY_INJECT_PREFIX = "以下是用户长期信息，仅在相关时自然使用，不要主动炫耀：\n"

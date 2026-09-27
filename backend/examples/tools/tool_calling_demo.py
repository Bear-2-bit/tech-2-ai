from langchain_core.messages import HumanMessage, ToolMessage
from langchain_deepseek import ChatDeepSeek

from app.ai.tools.calculator import calculator
from app.core.config import settings
import json



def main():
    model = ChatDeepSeek(
        model=settings.deepseek_model,
        api_key=settings.deepseek_api_key,
        api_base=settings.deepseek_base_url,
        temperature=0,
        max_tokens=500,
        timeout=settings.llm_timeout_seconds,
        max_retries=settings.llm_max_retries,
    )

    model_with_tools = model.bind_tools([
        calculator,
    ])

    messages = [
        HumanMessage(
            content="帮我计算 138 乘以 927"
        )
    ]

    # 第一次调用 LLM：
    # 模型决定是否调用工具，以及使用什么参数
    ai_message = model_with_tools.invoke(messages)

    print(json.dumps(
        ai_message.model_dump(),
        indent=2,
        ensure_ascii=False,
        default=str,
    ))

    if not ai_message.tool_calls:
        print("\n模型没有调用任何工具。")
        return

    tool_call = ai_message.tool_calls[0]

    # Python 真正执行工具
    tool_result = calculator.invoke(
        tool_call["args"]
    )

    print("\nTool Result：")
    print(tool_result)

    # 把模型提出的 ToolCall 加入消息历史
    messages.append(ai_message)

    # 把 Python 执行结果告诉模型
    tool_message = ToolMessage(
        content=str(tool_result),
        tool_call_id=tool_call["id"],
    )

    messages.append(tool_message)

    # 第二次调用 LLM：
    # 根据工具结果生成最终自然语言回答
    final_message = model_with_tools.invoke(messages)

    print("\nFinal Answer：")
    print(final_message.content)


if __name__ == "__main__":
    main()
from langchain_core.messages import HumanMessage, ToolMessage
from langchain_deepseek import ChatDeepSeek

from app.ai.tools.registry import tool_registry, tools
from app.core.config import settings


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

    model_with_tools = model.bind_tools(tools)

    messages = [
        HumanMessage(
            content="帮我计算 138 乘以 927，同时告诉我 tech-2-ai 有多少个字符。"
        )
    ]

    ai_message = model_with_tools.invoke(messages)

    import json
    print(json.dumps(
        ai_message.model_dump(),
        indent=2,
        ensure_ascii=False,
        default=str,
    ))

    if not ai_message.tool_calls:
        print("\n模型没有调用工具。")
        print(ai_message.content)
        return

    messages.append(ai_message)

    for tool_call in ai_message.tool_calls:
        tool_name = tool_call["name"]
        tool_args = tool_call["args"]

        tool = tool_registry.get(tool_name)

        if tool is None:
            tool_result = f"Tool not found: {tool_name}"
        else:
            try:
                tool_result = tool.invoke(tool_args)
            except Exception as exc:
                tool_result = f"Tool execution failed: {exc}"

        print(f"\nTool: {tool_name}")
        print("Args:", tool_args)
        print("Result:", tool_result)

        messages.append(
            ToolMessage(
                content=str(tool_result),
                tool_call_id=tool_call["id"],
            )
        )

    final_message = model_with_tools.invoke(messages)

    print("\nFinal Answer:")
    print(final_message.content)


if __name__ == "__main__":
    main()
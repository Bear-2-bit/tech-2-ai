# # 1 LLM Agent
# from app.agent import Agent
# from app.deepseek import DeepSeekClient
#
#
# def main():
#     llm = DeepSeekClient()
#
#     agent = Agent(
#         llm=llm,
#         max_steps=10,
#     )
#
#     question = input("User> ")
#
#     answer = agent.run(question)
#
#     print(f"\nAgent> {answer}")
#
#
# if __name__ == "__main__":
#     main()


# # 2 Langchain Agent
# from dotenv import load_dotenv
# from app.langchain_agent import create_my_agent
#
#
# load_dotenv()
#
#
# def main():
#     agent = create_my_agent()
#
#     question = input("User> ")
#
#     result = agent.invoke(
#         {
#             "messages": [
#                 {
#                     "role": "user",
#                     "content": question,
#                 }
#             ]
#         },
#         {
#             "recursion_limit": 20
#         },
#     )
#
#     final_message = result["messages"][-1]
#
#     print(
#         f"\nAgent> {final_message.content}"
#     )
#     print("---"*30)
#     from pprint import pprint
#     pprint(result["messages"])
#
# if __name__ == "__main__":
#     main()


# 3 MCP Agent
import asyncio
from dotenv import load_dotenv
from app.mcp_agent import create_my_agent
load_dotenv()


async def main():
    agent = await create_my_agent()

    question = input("User> ")

    result = await agent.ainvoke(
        {
            "messages": [
                {
                    "role": "user",
                    "content": question,
                }
            ]
        },
        {
            "recursion_limit": 20,
        },
    )

    final_message = result["messages"][-1]
    print(
        f"\nAgent> {final_message.content}"
    )
    print("---"*30)
    from pprint import pprint
    pprint(result["messages"])

if __name__ == "__main__":
    asyncio.run(main())
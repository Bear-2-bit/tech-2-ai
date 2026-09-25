import asyncio
import json

from langchain_core.prompts import ChatPromptTemplate
from langgraph.graph import END, START, StateGraph
from pydantic import BaseModel, Field
from typing_extensions import TypedDict

from app.dependencies import (
    get_langchain_model,
    get_rag_service,
    get_sql_service,
)
from app.schemas.rag import RAGRequest
from app.schemas.sql import SQLRequest


class AnalysisPlan(BaseModel):
    sql_question: str = Field(description="需要通过业务数据库回答的问题")
    rag_question: str = Field(description="需要通过企业知识库回答的问题")


class BusinessAnalysisReport(BaseModel):
    title: str = Field(description="报告标题")
    summary: str = Field(description="经营分析总结")
    key_findings: list[str] = Field(description="关键发现")
    recommendations: list[str] = Field(description="经营建议")


class WorkflowState(TypedDict, total=False):
    query: str

    sql_question: str
    rag_question: str

    sql_result: str
    rag_result: str

    report: dict


async def planner_node(state: WorkflowState) -> dict:
    model = get_langchain_model()

    structured_model = model.with_structured_output(
        AnalysisPlan,
        method="json_mode",
    )

    prompt = ChatPromptTemplate.from_messages([
        (
            "system",
            """
你是企业经营分析任务规划器。

请把用户任务拆成两个子问题：

1. sql_question
用于查询结构化业务数据库，
例如销售额、部门排名、订单统计等。

2. rag_question
用于查询企业知识库，
例如经营经验、业务规则、分析方法、建议依据等。

严格返回JSON。
""",
        ),
        (
            "human",
            "{query}",
        ),
    ])

    chain = prompt | structured_model

    plan = await chain.ainvoke({
        "query": state["query"],
    })

    return {
        "sql_question": plan.sql_question,
        "rag_question": plan.rag_question,
    }


async def sql_node(state: WorkflowState) -> dict:
    service = get_sql_service()

    result = await service.query(
        SQLRequest(
            question=state["sql_question"],
            max_rows=50,
        )
    )

    return {
        "sql_result": json.dumps(
            result.model_dump(),
            ensure_ascii=False,
        )
    }


async def rag_node(state: WorkflowState) -> dict:
    service = get_rag_service()

    result = await service.rag(
        RAGRequest(
            query=state["rag_question"],
            top_k=3,
        )
    )

    return {
        "rag_result": json.dumps(
            result.model_dump(),
            ensure_ascii=False,
        )
    }


async def synthesis_node(state: WorkflowState) -> dict:
    model = get_langchain_model()

    structured_model = model.with_structured_output(
        BusinessAnalysisReport,
        method="json_mode",
    )

    prompt = ChatPromptTemplate.from_messages([
        (
            "system",
            """
你是企业经营分析助手。

请综合用户原始任务、数据库查询结果和企业知识库结果，
生成一份结构化经营分析报告。

要求：
1. 数据事实必须以数据库查询结果为依据。
2. 经营建议必须结合知识库内容。
3. 不要编造输入中不存在的数据。
4. 严格返回JSON。
""",
        ),
        (
            "human",
            """
用户任务：
{query}

数据库结果：
{sql_result}

知识库结果：
{rag_result}
""",
        ),
    ])

    chain = prompt | structured_model

    report = await chain.ainvoke({
        "query": state["query"],
        "sql_result": state["sql_result"],
        "rag_result": state["rag_result"],
    })

    return {
        "report": report.model_dump(),
    }


def build_workflow():
    builder = StateGraph(WorkflowState)

    builder.add_node("planner", planner_node)
    builder.add_node("sql", sql_node)
    builder.add_node("rag", rag_node)
    builder.add_node("synthesis", synthesis_node)

    builder.add_edge(START, "planner")

    builder.add_edge("planner", "sql")
    builder.add_edge("planner", "rag")

    builder.add_edge(
        ["sql", "rag"],
        "synthesis",
    )

    builder.add_edge("synthesis", END)

    return builder.compile()


async def main():
    workflow = build_workflow()

    result = await workflow.ainvoke({
        "query": (
            "分析目前各部门的销售情况，"
            "并结合企业知识库给出经营建议。"
        )
    })

    print("SQL Question:")
    print(result["sql_question"])

    print("\nRAG Question:")
    print(result["rag_question"])

    print("\nSQL Result:")
    print(result["sql_result"])

    print("\nRAG Result:")
    print(result["rag_result"])

    print("\nStructured Report:")
    print(
        json.dumps(
            result["report"],
            ensure_ascii=False,
            indent=2,
        )
    )


if __name__ == "__main__":
    asyncio.run(main())
from pydantic import BaseModel, Field


class WorkflowRequest(BaseModel):
    query: str = Field(min_length=1)


class AnalysisPlan(BaseModel):
    sql_question: str
    rag_question: str


class BusinessAnalysisReport(BaseModel):
    title: str = Field(description="经营分析报告标题")
    summary: str = Field(description="对整体经营情况的简要总结")
    key_findings: list[str] = Field(description="基于数据库结果得到的关键发现")
    recommendations: list[str] = Field(description="结合知识库内容得到的经营建议")


class WorkflowResponse(BaseModel):
    query: str
    sql_question: str
    rag_question: str
    sql_result: dict
    rag_result: dict
    report: BusinessAnalysisReport
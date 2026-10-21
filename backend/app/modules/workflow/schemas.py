from typing import Literal

from pydantic import BaseModel, Field


class ReportRequest(BaseModel):
    month: str = Field(default="2026-09", pattern=r"^20\d{2}-(0[1-9]|1[0-2])$")
    department_id: int | None = Field(default=None, ge=1, le=4)
    focus: str = Field(default="关注净销售额、退款与售后变化", max_length=1000)


class MetricFinding(BaseModel):
    metric: Literal[
        "sales_cents", "refund_cents", "net_sales_cents", "order_count", "ticket_count", "attainment", "net_growth"
    ]
    interpretation: str


class Advice(BaseModel):
    action: str
    evidence_ids: list[str] = Field(default_factory=list)


class Narrative(BaseModel):
    title: str
    summary: str
    findings: list[MetricFinding] = Field(min_length=2)
    recommendations: list[Advice] = Field(default_factory=list)
    uncertainties: list[str] = Field(default_factory=list)

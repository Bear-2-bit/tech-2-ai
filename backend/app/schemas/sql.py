from pydantic import BaseModel, Field


class SQLRequest(BaseModel):
    question: str = Field(min_length=1)
    max_rows: int = Field(default=100, ge=1, le=500)


class SQLGenerationResult(BaseModel):
    sql: str
    explanation: str


class SQLResponse(BaseModel):
    question: str
    sql: str
    explanation: str
    columns: list[str]
    rows: list[list]
    row_count: int
    truncated: bool
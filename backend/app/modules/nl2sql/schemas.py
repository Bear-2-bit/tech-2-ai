from pydantic import BaseModel, Field


class SQLRequest(BaseModel):
    question: str = Field(min_length=1, max_length=4000)
    max_rows: int = Field(default=100, ge=1, le=500)


class GeneratedSQL(BaseModel):
    sql: str = Field(min_length=1, max_length=12000)
    explanation: str

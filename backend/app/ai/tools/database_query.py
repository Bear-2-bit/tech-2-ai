import json
from collections.abc import Callable

from langchain_core.tools import tool

from app.schemas.sql import SQLRequest
from app.services.sql_service import SQLService


def create_database_query_tool(
    get_service: Callable[[], SQLService],
):
    @tool
    async def database_query(
        question: str,
        max_rows: int = 20,
    ) -> str:
        """根据自然语言问题安全查询业务数据库。适合销售、订单、统计等结构化数据问题。"""

        service = get_service()

        result = await service.query(
            SQLRequest(
                question=question,
                max_rows=max_rows,
            )
        )

        return json.dumps(
            result.model_dump(),
            ensure_ascii=False,
        )

    return database_query
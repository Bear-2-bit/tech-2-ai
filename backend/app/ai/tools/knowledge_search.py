import json
from collections.abc import Callable

from langchain_core.tools import tool

from app.schemas.search import SearchRequest
from app.services.search_service import SearchService


def create_knowledge_search_tool(
    get_service: Callable[[], SearchService],
):
    @tool
    async def knowledge_search(
        query: str,
        top_k: int = 3,
    ) -> str:
        """从企业知识库中检索与问题相关的文档。适合查询知识库、文档、资料中的信息。"""

        service = get_service()

        result = await service.search(
            SearchRequest(
                query=query,
                top_k=top_k,
            )
        )

        return json.dumps(
            result.model_dump(),
            ensure_ascii=False,
        )

    return knowledge_search
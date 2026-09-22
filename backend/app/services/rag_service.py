import asyncio

from langchain_core.documents import Document
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_deepseek import ChatDeepSeek
from langchain_qdrant import QdrantVectorStore

from app.ai.retrieval.query_rewriter import QueryRewriter
from app.ai.retrieval.reranker import Reranker
from app.schemas.rag import (
    RAGCitation,
    RAGDocument,
    RAGRequest,
    RAGResponse,
)


class RAGService:
    def __init__(
        self,
        vector_store: QdrantVectorStore,
        model: ChatDeepSeek,
        query_rewriter: QueryRewriter,
        reranker: Reranker,
    ):
        self.vector_store = vector_store
        self.query_rewriter = query_rewriter
        self.reranker = reranker

        prompt = ChatPromptTemplate.from_messages([
            (
                "system",
                """
                    你是一个企业知识库问答助手。

                    请严格根据提供的知识库内容回答问题。

                    要求：
                    1. 不得使用知识库之外的信息进行补充。
                    2. 如果知识不足，请明确回答：“根据当前知识库内容无法确定。”
                    3. 回答中引用知识时，请使用 [1]、[2] 这样的来源编号。
                    4. 只能引用实际支持该结论的来源。
                    5. 不要编造来源。

                    知识库内容：

                    {context}
                """,
            ),
            (
                "human",
                "{query}",
            ),
        ])

        self.chain = prompt | model | StrOutputParser()

    async def rag(self, request: RAGRequest) -> RAGResponse:
        rewritten_query = await self.query_rewriter.rewrite(request.query)

        candidate_k = min(max(request.top_k * 4, 10), 50)

        retriever = self.vector_store.as_retriever(
            search_kwargs={"k": candidate_k}
        )

        candidate_documents = await retriever.ainvoke(rewritten_query)

        reranked_documents = await asyncio.to_thread(
            self.reranker.rerank,
            rewritten_query,
            candidate_documents,
            request.top_k,
        )

        context = self._build_context(reranked_documents)

        answer = await self.chain.ainvoke({
            "query": request.query,
            "context": context,
        })

        retrieved_documents = [
            RAGDocument(
                content=document.page_content,
                metadata=document.metadata,
                rerank_score=score,
            )
            for document, score in reranked_documents
        ]

        citations = self._build_citations(reranked_documents)

        return RAGResponse(
            query=request.query,
            rewritten_query=rewritten_query,
            answer=answer,
            retrieved_documents=retrieved_documents,
            citations=citations,
        )

    def _build_context(
        self,
        documents: list[tuple[Document, float]],
    ) -> str:
        if not documents:
            return "当前没有可用的知识库内容。"

        blocks = []

        for index, (document, _) in enumerate(documents, start=1):
            source = document.metadata.get("filename") or document.metadata.get("source") or "unknown"
            page = document.metadata.get("page_label")

            if page is not None:
                location = f"{source}，第{page}页"
            else:
                location = source

            blocks.append(
                f"[{index}] 来源：{location}\n{document.page_content}"
            )

        return "\n\n".join(blocks)

    def _build_citations(
        self,
        documents: list[tuple[Document, float]],
    ) -> list[RAGCitation]:
        citations = []

        for index, (document, _) in enumerate(documents, start=1):
            metadata = document.metadata

            citations.append(
                RAGCitation(
                    index=index,
                    source=metadata.get("filename") or metadata.get("source") or "unknown",
                    page=metadata.get("page_label"),
                    chunk_index=metadata.get("chunk_index"),
                )
            )

        return citations
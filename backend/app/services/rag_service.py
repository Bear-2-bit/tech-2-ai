from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_deepseek import ChatDeepSeek
from langchain_qdrant import QdrantVectorStore

from app.schemas.rag import RAGDocument, RAGRequest, RAGResponse


class RAGService:
    def __init__(self, vector_store: QdrantVectorStore, model: ChatDeepSeek):
        self.vector_store = vector_store

        prompt = ChatPromptTemplate.from_messages([
            (
                "system",
                """
                    你是一个企业知识库问答助手。

                    请严格根据提供的知识库内容回答用户问题。

                    如果知识库内容不足以回答，请明确回答：
                    “根据当前知识库内容无法确定。”

                    不要编造知识库中不存在的信息。

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
        retriever = self.vector_store.as_retriever(
            search_kwargs={"k": request.top_k}
        )

        documents = await retriever.ainvoke(request.query)

        context = "\n\n".join(
            document.page_content for document in documents
        )

        answer = await self.chain.ainvoke({
            "query": request.query,
            "context": context,
        })

        retrieved_documents = [
            RAGDocument(
                content=document.page_content,
                metadata=document.metadata,
            )
            for document in documents
        ]

        return RAGResponse(
            query=request.query,
            answer=answer,
            retrieved_documents=retrieved_documents,
        )
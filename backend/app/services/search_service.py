from langchain_qdrant import QdrantVectorStore

from app.schemas.search import SearchDocument, SearchRequest, SearchResponse


class SearchService:
    def __init__(self, vector_store: QdrantVectorStore):
        self.vector_store = vector_store

    async def search(self, request: SearchRequest) -> SearchResponse:
        retriever = self.vector_store.as_retriever(search_kwargs={"k": request.top_k})
        documents = await retriever.ainvoke(request.query)

        results = [
            SearchDocument(content=document.page_content, metadata=document.metadata)
            for document in documents
        ]

        return SearchResponse(query=request.query, documents=results)
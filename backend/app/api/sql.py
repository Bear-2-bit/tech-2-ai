from fastapi import APIRouter, Depends

from app.dependencies import get_sql_service
from app.schemas.sql import SQLRequest, SQLResponse
from app.services.sql_service import SQLService


router = APIRouter(
    prefix="/api/sql",
    tags=["sql"],
)


@router.post("", response_model=SQLResponse)
async def query_sql(
    request: SQLRequest,
    sql_service: SQLService = Depends(get_sql_service),
) -> SQLResponse:
    return await sql_service.query(request)
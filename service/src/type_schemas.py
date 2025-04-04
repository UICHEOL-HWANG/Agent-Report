from pydantic import BaseModel, Field
from typing import Annotated


class YouTubeSummaryInput(BaseModel):
    query: Annotated[str, Field(description="YouTube에서 검색할 키워드입니다.")]
from typing import List

from pydantic import BaseModel, Field


class Page(BaseModel):
    title: str
    url: str
    keywords: List[str] = Field(default_factory=list)


class LinkRecommendation(BaseModel):
    anchor_text: str
    target_url: str
    relevance_score: int
    placement_suggestion: str
    reasoning: str


class LinkGenerateRequest(BaseModel):
    text: str
    pages: List[Page]
    target_keywords: List[str] | None = None
    min_relevance: int = 70
    max_links: int = 5


class LinkGenerateResponse(BaseModel):
    links: List[LinkRecommendation]

from typing import List

from app.schemas.link import LinkGenerateRequest, LinkRecommendation


def _score(page_keywords: List[str], target_keywords: List[str]) -> int:
    if not target_keywords:
        return 100
    matches = len(set(page_keywords) & set(target_keywords))
    return int(100 * matches / len(target_keywords))


def generate_links(payload: LinkGenerateRequest) -> List[LinkRecommendation]:
    recommendations: List[LinkRecommendation] = []
    for page in payload.pages:
        score = _score(page.keywords, payload.target_keywords or [])
        if score < payload.min_relevance:
            continue
        recommendation = LinkRecommendation(
            anchor_text=page.title,
            target_url=page.url,
            relevance_score=score,
            placement_suggestion="Introduction",
            reasoning="Keyword match",
        )
        recommendations.append(recommendation)
        if len(recommendations) >= payload.max_links:
            break
    return recommendations

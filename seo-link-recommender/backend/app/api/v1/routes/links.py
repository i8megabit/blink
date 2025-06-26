from app.schemas.link import LinkGenerateRequest, LinkGenerateResponse
from app.services.link_generator import generate_links
from fastapi import APIRouter, HTTPException

router = APIRouter()


@router.post("/generate", response_model=LinkGenerateResponse)
async def generate_link_recommendations(
    payload: LinkGenerateRequest,
) -> LinkGenerateResponse:
    try:
        links = generate_links(payload)
    except ValueError as err:
        raise HTTPException(status_code=400, detail=str(err)) from err
    return LinkGenerateResponse(links=links)

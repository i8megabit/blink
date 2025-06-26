from app.schemas.link import LinkGenerateRequest, Page
from app.services.link_generator import _score, generate_links


def test_score_no_targets():
    assert _score(["a"], []) == 100


def test_score_with_targets():
    assert _score(["a", "b"], ["b", "c"]) == 50


def test_generate_links_respects_min_score_and_limit():
    pages = [
        Page(title="Page1", url="/1", keywords=["a"]),
        Page(title="Page2", url="/2", keywords=["b"]),
        Page(title="Page3", url="/3", keywords=["c"]),
    ]
    payload = LinkGenerateRequest(
        text="", pages=pages, target_keywords=["b"], max_links=1
    )
    links = generate_links(payload)
    assert len(links) == 1
    assert links[0].target_url == "/2"

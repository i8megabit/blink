# SEO Link Recommender

This project demonstrates a simplified backend for generating SEO link recommendations.

## Development

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r backend/requirements.txt
uvicorn app.main:app --reload --app-dir backend/app
```

Run tests:

```bash
pytest backend/tests --cov=backend/app
```

# Quick Start on macOS

This repository currently contains no application code on the `main` branch.
To restore the previously merged code, create a separate branch from commit
`c330bae` and work there.

```bash
# clone the repository
git clone <repo-url> project
cd project

# create a new branch from the previous commit
git checkout -b feature/app c330bae
```

## Running the backend
Install Python 3.11 and [Homebrew](https://brew.sh/) if not already installed.

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r seo-link-recommender/backend/requirements.txt
uvicorn app.main:app --app-dir seo-link-recommender/backend/app --reload
```

## Docker services
Make sure Docker Desktop is installed and running. Then launch all services:

```bash
docker compose -f seo-link-recommender/docker-compose.yml up --build
```

## Testing

```bash
pytest seo-link-recommender/backend/tests --cov=seo-link-recommender/backend/app
```

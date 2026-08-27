# ListingIQ

AI-powered Shopify listing optimizer.

## v1 scope
Paste a product title and description, get back an optimized version plus
an explanation of what was weak about the original.

## Setup
```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env    # then paste your real API key into .env
```

## Run
```bash
python src/optimize.py          # smoke test - one listing, prints to terminal
streamlit run src/app.py        # the UI (not built yet)
```

## Roadmap
- v1 - paste in, optimized listing out (Streamlit + Claude)
- v2 - pull listings directly from Shopify (read-only)
- v3 - track what happened after the change
- v4 - ML layer: model what actually converts per category
- v5 - write-back, OAuth, App Store

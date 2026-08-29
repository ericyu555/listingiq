# ListingIQ

AI-powered Shopify listing optimizer.

## v1 scope
Paste a product title and description, get back an optimized version plus
an explanation of what was weak about the original.

## Setup

> **The venv lives OUTSIDE this folder, at `~/venvs/listingiq`, on purpose.**
> `~/Desktop` is iCloud-synced. A venv is ~12,000 files, and syncing them made
> `import streamlit` take **137 seconds** instead of 1. Venvs are machine-specific
> and rebuildable - they should never sit in a synced folder.

```bash
python3 -m venv ~/venvs/listingiq
~/venvs/listingiq/bin/pip install -r requirements.txt
cp .env.example .env    # then paste your real API key into .env
```

## Run
```bash
# smoke test - one hardcoded listing, prints to terminal
~/venvs/listingiq/bin/python src/optimize.py

# the UI
~/venvs/listingiq/bin/streamlit run src/app.py
```

## Roadmap

- v1 - paste in, optimized listing out (Streamlit + Claude) **[done]**
- v2 - pull listings directly from Shopify (read-only), batch the whole catalogue
- v3 - **outcome tracking**: record what happened after each change
- v3.5 - own-data pricing insight (needs v3 data)
- v4 - ML layer: model what actually converts per category (needs v3 data)
- v5 - write-back, OAuth, App Store

### Why this order
The ML layer and pricing both need **conversion data**, and there isn't any until
v3 exists. That isn't a scheduling preference - it's a dependency. Anything built
before v3 would be the model's prior dressed up as analysis.

### Notes for later
- **Batching:** at ~20-60s per product, a 200-product store takes hours serially.
  Anthropic's Batch API handles this asynchronously at 50% cost.
- **Outcome tracking is an A/B test.** Optimize half the catalogue, leave half as
  a control. Pick the decision metric before launch.
- **Traffic is the constraint.** A product at 50 sessions/week and 2% conversion
  makes one sale a week - per-product significance is unreachable. Pool across
  products (and later stores), and watch leading indicators (sessions,
  add-to-cart) rather than purchases alone.
- **Competitive pricing** needs competitor data Shopify won't give you. Scraping
  is fragile, feeds are expensive. Revisit only if paying users ask for it.

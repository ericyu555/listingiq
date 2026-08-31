"""
ListingIQ - catalogue enricher.

Reads a Shopify store's public product feed, extracts the facts already
written in each description, and produces tags, product_type, and SEO
title/description. Product titles are left alone.

Output is a CSV the store owner reviews and imports herself.

    ~/venvs/listingiq/bin/python src/enrich.py --store your-store-name --limit 5
    ~/venvs/listingiq/bin/python src/enrich.py --store your-store-name
"""

import argparse
import csv
import html
import re
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed

import requests
from pydantic import BaseModel
from dotenv import load_dotenv
import anthropic

load_dotenv()
client = anthropic.Anthropic()
MODEL = "claude-opus-5"


# ---------------------------------------------------------------------------
# TODO 1 - the fields to pull out of each listing.
#
# Same idea as OptimizedListing in optimize.py: you're describing the shape
# of the answer. Types you need are `str` and `list[str]`.
#
# For the fact fields, the prompt tells Claude to write "not stated" when the
# listing doesn't say - so they're all plain `str`, never missing.
# ---------------------------------------------------------------------------

class ListingFields(BaseModel):
    brand: str             # <- "Eddie Bauer", or "not stated"
    garment_type: str      # <- "Polo", "Sweater", "Shorts"
    color: str             # <- "purple", or "not stated"
    size: str              # <- "Small", or "not stated"
    material: str          # <- "100% cotton", or "not stated"
    condition: str         # <- "excellent", or "not stated"
    tags: list[str]        # <- 6-10 searchable tags
    seo_title: str         # <- under 60 characters
    seo_description: str   # <- around 155 characters


SYSTEM_PROMPT = """You extract structured fields from secondhand listings for a
thrift shop that sells both clothing and home decor.

Your job is EXTRACTION, not invention. Every value must come from the listing text.

FACT FIELDS (brand, color, size, material, condition)
- If the listing does not state something, write exactly "not stated". Never guess
  a brand, material, color, or era from the product name or the type of item.
- These fields are for the seller's internal review. They never appear in copy.

garment_type - choose EXACTLY ONE, copied verbatim from this list:
  Apparel: Sweater, Cardigan, Sweatshirt, Tee, Tank, Blouse, Shirt, Button-Down,
           Polo, Quarter Zip, Dress, Skirt, Shorts, Pants, Jeans, Jacket, Coat,
           Vest, Shoes, Bag, Accessory
  Home:    Print, Plate, Mug, Basket, Matchbox, Candle, Ornament, Sticker, Home Decor
  Fallback: Other
  Never invent a category. Never write "not stated" here. If nothing fits, use Other.

tags - 6 to 10 tags, all lowercase. Use these forms exactly so filters work:
- garment type: the chosen type, lowercased ("button-down", "quarter zip")
- brand: as written, lowercased. Omit entirely if not stated.
- color: give the BASE color from this list, plus the seller's specific shade if
  she named one. black, white, grey, brown, tan, cream, red, pink, orange, yellow,
  green, blue, purple, navy, multicolor. So butter yellow becomes two tags:
  "yellow" and "butter yellow". Omit both if no color is stated.
- size: bare and lowercase. xs, s, m, l, xl, xxl, or the numeric size ("7.5", "14").
  Never "size l", never "large", never "mens large".
- material: base fiber only. cotton, silk, wool, linen, denim, leather, polyester,
  nylon, rayon, cashmere. Omit if not stated.
- condition: one of "excellent", "very good", "good", "fair". Omit if not stated.
- "vintage" only if the listing says vintage.
- Up to two descriptive tags for a print or motif ("golf cart print", "novelty print").
- Never tag the store name, or generic words like "clothing", "secondhand", "item".

seo_title - what Google should show. Lead with brand and garment type, then color
and size. AT MOST 60 characters. No em-dashes, use commas.

seo_description - AT MOST 155 characters, written to earn a click.
- State only facts the listing gives: brand, type, color, size, material, condition,
  key measurement.
- NEVER mention what is missing. Do not write "brand is not stated" or anything
  like it. If a fact is absent, simply leave it out.
- Never claim scarcity, stock level, or uniqueness.
- No em-dashes.
- If the listing is nearly empty, write one short honest sentence from what exists.
"""


def strip_html(raw: str) -> str:
    text = html.unescape(re.sub(r"<[^>]+>", "\n", raw or ""))
    return re.sub(r"\n{2,}", "\n", text).strip()


def fetch_products(store: str) -> list[dict]:
    url = f"https://{store}.myshopify.com/products.json?limit=250"
    r = requests.get(url, timeout=30)
    r.raise_for_status()
    return r.json().get("products", [])


def enrich(title: str, description: str) -> ListingFields:
    """Extract structured fields from one listing."""

    user_message = f"""Extract the fields from this listing.

TITLE:
{title}

DESCRIPTION:
{description}"""

    # -----------------------------------------------------------------------
    # TODO 2 - the API call. Same five arguments as optimize.py, plus one:
    #
    #     output_config={"effort": "low"}
    #
    # This is a mechanical extraction, so it doesn't need deep reasoning.
    # Low effort makes it faster and cheaper without changing the model.
    #
    # Then return response.parsed_output
    # -----------------------------------------------------------------------

    response =  client.messages.parse(
        model=MODEL,
        max_tokens=16000,
        system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": user_message}],
        output_format=ListingFields,
        output_config={"effort": "low"},
    )  # <- your call here
    return response.parsed_output


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--store", required=True, help="the myshopify subdomain")
    ap.add_argument("--limit", type=int, help="only process the first N (test runs)")
    ap.add_argument("--workers", type=int, default=8)
    ap.add_argument("--out", default="enriched.csv")
    args = ap.parse_args()

    products = fetch_products(args.store)
    if args.limit:
        products = products[: args.limit]
    print(f"{len(products)} products to process, {args.workers} at a time")

    rows, failures = [], []
    started = time.time()

    def work(p):
        return p, enrich(p["title"], strip_html(p.get("body_html")))

    with ThreadPoolExecutor(max_workers=args.workers) as pool:
        futures = [pool.submit(work, p) for p in products]
        for n, fut in enumerate(as_completed(futures), 1):
            try:
                p, f = fut.result()
            except Exception as e:
                failures.append(str(e))
                print(f"  [{n}/{len(products)}] FAILED: {e}", file=sys.stderr)
                continue
            rows.append({
                "Handle": p["handle"],
                "Title": p["title"],          # unchanged, included so import is safe
                "Type": f.garment_type,
                "Tags": ", ".join(f.tags),
                "SEO Title": f.seo_title,
                "SEO Description": f.seo_description,
                "_brand": f.brand,            # underscore columns are for review only
                "_color": f.color,
                "_size": f.size,
                "_material": f.material,
                "_condition": f.condition,
            })
            print(f"  [{n}/{len(products)}] {p['title']}")

    rows.sort(key=lambda r: r["Handle"])
    with open(args.out, "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)

    print(f"\ndone in {time.time()-started:.0f}s")
    print(f"wrote {len(rows)} rows to {args.out}" + (f", {len(failures)} failed" if failures else ""))
    print("\nReview it, delete the _underscore columns, then it's ready for Shopify import.")


if __name__ == "__main__":
    main()

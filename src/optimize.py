"""
ListingIQ - core optimizer.

Smoke test: run this directly to optimize one hardcoded listing.
    ~/venvs/listingiq/bin/python src/optimize.py
"""

import os
from pydantic import BaseModel
from dotenv import load_dotenv
import anthropic

load_dotenv()
client = anthropic.Anthropic()   # reads ANTHROPIC_API_KEY from .env

MODEL = "claude-opus-5"


# ---------------------------------------------------------------------------
# TODO 1 - describe the shape of the answer you want back.
#
# Pydantic models are how you tell Claude "return exactly these fields".
# The SDK turns this class into a schema, sends it along, and validates
# the reply against it - so you get a real Python object, not a blob of
# text you have to parse.
#
# Fill in the fields. Syntax is `name: type`. Types you need:
#     str          a single string
#     list[str]    a list of strings
#     list[Issue]  a list of Issue objects
# ---------------------------------------------------------------------------

class Issue(BaseModel):
    problem: str            # what's weak about the original
    why_it_matters: str     # why a shopper or search engine cares


class OptimizedListing(BaseModel):
    title: str              # <- the rewritten product title
    description: str        # <- the rewritten description
    bullets: list[str]    # <- 3-5 short selling points
    meta_description: str   # <- ~155 chars for search results
    issues: list[Issue]              # <- what was wrong with the original


SYSTEM_PROMPT = """You are an expert Shopify listing optimizer.

You rewrite product listings to convert better without inventing facts.

Rules:
- Never invent a material, measurement, certification, or claim that is not
  in the original. If the original does not say it, you may not say it.
  This includes inferences: do not say how a product feels, fits, wears,
  performs, or compares unless the original says so.
- Titles: lead with what the product IS, then the differentiator. Keep under
  70 characters so it does not truncate in search results.
- Descriptions: open with the benefit, not the feature. Short paragraphs.
- Bullets: concrete and scannable. No marketing filler like "high quality".
- Meta description: around 155 characters, written to earn a click.
- Match the voice of the original. A minimalist brand should not suddenly
  sound like an infomercial.

For `issues`, list what was actually weak in the original - be specific and
name the real problem, not generic advice. Report at most 5, ordered most
important first - pick the ones costing the most sales, not every flaw you
can find."""


def optimize(title: str, description: str) -> OptimizedListing:
    """Send one listing to Claude, get a structured rewrite back."""

    user_message = f"""Optimize this Shopify product listing.

CURRENT TITLE:
{title}

CURRENT DESCRIPTION:
{description}"""

    # -----------------------------------------------------------------------
    # TODO 2 - make the API call.
    #
    # Use client.messages.parse(...) - the "parse" version is what enforces
    # your Pydantic model. Plain .create() would just give you text back.
    #
    # It needs five arguments:
    #     model=          the MODEL constant above
    #     max_tokens=     16000 is a safe default
    #     system=         the SYSTEM_PROMPT above
    #     messages=       [{"role": "user", "content": user_message}]
    #     output_format=  the class you defined in TODO 1
    #
    # Then return response.parsed_output
    # -----------------------------------------------------------------------

    response = client.messages.parse(
        model=MODEL,
        max_tokens=16000,
        system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": user_message}],
        output_format=OptimizedListing,
    )   # <- your call here
    return response.parsed_output


if __name__ == "__main__":
    result = optimize(
        title="Sorel",
        description="Size 9 Sneakers Excellent Condition",
    )

    print("TITLE:", result.title)
    print()
    print("DESCRIPTION:", result.description)
    print()
    print("BULLETS:")
    for b in result.bullets:
        print("  -", b)
    print()
    print("META:", result.meta_description)
    print()
    print("ISSUES WITH THE ORIGINAL:")
    for i in result.issues:
        print(f"  - {i.problem}\n    why: {i.why_it_matters}")

---
phase: quick
plan: 1
type: execute
wave: 1
depends_on: []
files_modified:
  - backend/app/core/config.py
  - backend/.env
  - backend/mcp_server/tools/product_compose.py
  - backend/mcp_server/tools/product_affiliate.py
autonomous: true
requirements: [UNCLE-MIKE-01]

must_haves:
  truths:
    - "Product responses always follow Blog Review -> Product Cards (max 5) -> Follow-up Questions format"
    - "When USE_CURATED_LINKS=true, curated amzn.to links are used as primary product source instead of live API search"
    - "Every product response includes contextual follow-up suggestions in the assistant_text (not just next_step_suggestion tool)"
    - "Product cards are capped at 5 per response"
  artifacts:
    - path: "backend/app/core/config.py"
      provides: "USE_CURATED_LINKS feature flag"
      contains: "USE_CURATED_LINKS"
    - path: "backend/.env"
      provides: "USE_CURATED_LINKS=true default"
      contains: "USE_CURATED_LINKS=true"
    - path: "backend/mcp_server/tools/product_compose.py"
      provides: "Updated blog_article system prompt enforcing Uncle Mike format + inline follow-ups"
    - path: "backend/mcp_server/tools/product_affiliate.py"
      provides: "Curated-first logic gated by USE_CURATED_LINKS flag"
  key_links:
    - from: "backend/mcp_server/tools/product_affiliate.py"
      to: "backend/app/core/config.py"
      via: "settings.USE_CURATED_LINKS"
      pattern: "settings\\.USE_CURATED_LINKS"
    - from: "backend/mcp_server/tools/product_compose.py"
      to: "product_affiliate.py curated data"
      via: "state['affiliate_products'] from curated links"
      pattern: "affiliate_products"
---

<objective>
Implement Uncle Mike's feedback on response format: enforce Blog Review -> Product Carousel (5 links) -> Conversational Follow-up structure for every product response. Add USE_CURATED_LINKS feature flag so curated amzn.to links are the primary product source until PA-API access is granted.

Purpose: Fix product response format to match the editorial blog style Uncle Mike expects, and ensure curated affiliate links (tag: mikejahshan-20) are used reliably instead of live API calls that may return inconsistent/empty results.

Output: Updated backend config, product_affiliate (curated-first logic), and product_compose (enforced response format with inline follow-ups).
</objective>

<execution_context>
@C:/Users/habib/.claude/get-shit-done/workflows/execute-plan.md
@C:/Users/habib/.claude/get-shit-done/templates/summary.md
</execution_context>

<context>
@backend/app/core/config.py
@backend/mcp_server/tools/product_compose.py
@backend/mcp_server/tools/product_affiliate.py
@backend/app/services/affiliate/providers/curated_amazon_links.py
@backend/mcp_server/tools/next_step_suggestion.py

<interfaces>
<!-- Key types and contracts the executor needs -->

From backend/app/services/affiliate/providers/curated_amazon_links.py:
```python
# CURATED_LINKS dict maps keyword -> list of product dicts
# Each product: {"url": str, "title": str, "price": float, "asin": str, "image_url": str}
def find_curated_links(query: str) -> list[dict] | None:
    """Find curated Amazon product data matching a query. Returns list of product dicts or None."""
```

From backend/app/core/config.py:
```python
class Settings(BaseSettings):
    MAX_PRODUCTS_RETURN: int = Field(default=5, ...)
    # USE_CURATED_LINKS will be added here
```

From backend/mcp_server/tools/product_affiliate.py (lines 102-202):
```python
# Curated link lookup already exists — currently ALWAYS runs before live API
# When curated links found, they are used for Amazon provider results
# The new flag should make curated links the ONLY source when enabled
```

From backend/mcp_server/tools/product_compose.py:
```python
# blog_article LLM task (line 682-705): system prompt for blog-style article
# concierge LLM task (line 445-454): system prompt for non-review responses
# conclusion LLM task (line 568-577): follow-up question generation
# products_by_provider dict: all affiliate products grouped by provider
# ui_blocks list: assembled UI blocks (product_review cards, review_sources, etc.)
# MAX cap: products_by_provider products are already sliced to [:10] per provider (line 406)
```
</interfaces>
</context>

<tasks>

<task type="auto">
  <name>Task 1: Add USE_CURATED_LINKS feature flag and enforce curated-first in product_affiliate</name>
  <files>backend/app/core/config.py, backend/.env, backend/mcp_server/tools/product_affiliate.py</files>
  <action>
**1. backend/app/core/config.py** — Add the USE_CURATED_LINKS setting to the Settings class, near the existing `USE_MOCK_AFFILIATE` field (around line 261):

```python
USE_CURATED_LINKS: bool = Field(
    default=True,
    description="Use curated Amazon affiliate links as primary product source (bypasses live product search APIs)"
)
```

**2. backend/.env** — Append this line after the existing settings (after the ENABLE_SEARCH_CACHE line, around line 30):

```
USE_CURATED_LINKS=true
```

**3. backend/mcp_server/tools/product_affiliate.py** — Modify the `product_affiliate` function to enforce curated-first when flag is on:

At the top of the function (after the existing curated link lookup block, ~line 110), add a **curated-only early return** when the flag is enabled:

```python
if curated_amazon_links and settings.USE_CURATED_LINKS:
    # When USE_CURATED_LINKS is on, curated links are the ONLY source.
    # Skip all live API provider searches.
    results = []
    for i, product_name in enumerate(products_to_search):
        if i < len(curated_amazon_links):
            curated = curated_amazon_links[i]
            if isinstance(curated, dict):
                link = curated.get("url", "")
                title = curated.get("title", product_name)
                price = curated.get("price", 0)
                image = curated.get("image_url", "")
            else:
                link = curated
                title = product_name
                price = 0
                image = ""
            results.append({
                "product_name": product_name,
                "offers": [{
                    "product_id": f"curated-{curated.get('asin', i)}" if isinstance(curated, dict) else f"curated-{i}",
                    "title": title,
                    "price": price,
                    "currency": "USD",
                    "url": link,
                    "image_url": image,
                    "merchant": "Amazon",
                    "rating": None,
                    "review_count": None,
                    "source": "amazon",
                }]
            })
    # Cap at 5 products
    results = results[:5]
    logger.info(f"[product_affiliate] USE_CURATED_LINKS=true: returning {len(results)} curated Amazon links (skipping live APIs)")
    return {
        "affiliate_products": {"amazon": results} if results else {},
        "success": True
    }
```

Import settings at the top of the function body (it's already imported in the existing code via `from app.core.config import settings`; confirm it's accessible).

Also: in the existing `search_provider("amazon")` block (~line 171-202), cap the curated results to `[:5]` — change `if i < len(curated_amazon_links)` to `if i < min(len(curated_amazon_links), 5)`.

**IMPORTANT:** Do NOT remove the existing curated link fallback logic for when USE_CURATED_LINKS=false. The existing code path should continue to work when the flag is off (live APIs + curated as supplement).
  </action>
  <verify>
    <automated>cd /c/Users/habib/Downloads/ReviewGuide-SourceCode && python -c "from backend.app.core.config import Settings; s = Settings._model_fields; assert 'USE_CURATED_LINKS' in s, 'Missing USE_CURATED_LINKS'; print('OK: USE_CURATED_LINKS field exists')" 2>/dev/null || cd /c/Users/habib/Downloads/ReviewGuide-SourceCode/backend && python -c "import sys; sys.path.insert(0,'.'); from app.core.config import Settings; fields = Settings.model_fields if hasattr(Settings,'model_fields') else Settings.__fields__; assert 'USE_CURATED_LINKS' in fields; print('OK: USE_CURATED_LINKS field exists in Settings')"</automated>
  </verify>
  <done>USE_CURATED_LINKS=true exists in config.py and .env. product_affiliate.py returns curated-only results (capped at 5) when flag is on, and falls back to existing live API + curated supplement behavior when flag is off.</done>
</task>

<task type="auto">
  <name>Task 2: Enforce Uncle Mike response format in product_compose — Blog Review + 5 Product Cards + Follow-up Questions</name>
  <files>backend/mcp_server/tools/product_compose.py</files>
  <action>
**1. Update the blog_article system prompt** (line 683-698) to enforce the Uncle Mike structure. Replace the existing system prompt with:

```python
{"role": "system", "content": """You are an expert product journalist writing a buying guide for ReviewGuide.ai. Write in a warm, authoritative voice — like a Wirecutter or The Verge review.

FORMAT — FOLLOW THIS EXACT STRUCTURE EVERY TIME:

**SECTION 1: Blog Review (3-5 paragraphs)**
- Paragraph 1: What the user is looking for and what matters most in this category
- Paragraph 2-3: Summarize what reviewers say — reference specific reviewer insights using inline citations (e.g., "[Wirecutter](url) highlights..." or "According to [RTINGS](url)..."). Name the top picks and WHY reviewers recommend them.
- Paragraph 4: Brief mention of what to watch out for — common tradeoffs, things reviewers flag
- Final paragraph: A short verdict/recommendation summary

**SECTION 2: Follow-up Questions (MANDATORY)**
After your review, ALWAYS end with exactly 3 conversational follow-up questions to help the user explore further. Write them as a short paragraph starting with something like "Want to dig deeper?" followed by questions like:
- "Want to compare the top two head-to-head?"
- "Looking for budget alternatives under $X?"
- "Want more details on battery life and durability?"
- "Interested in seeing what real users say about these?"
- "Need help picking between [Product A] and [Product B]?"
Make the questions SPECIFIC to the products and category — not generic.

RULES:
- DO NOT write per-product ## headings or sections — the individual products are shown as interactive cards below your text
- DO NOT include product images, prices, or buy links — those are in the cards
- DO include review source names and citation links throughout the text
- Write naturally — vary sentence structure, don't be formulaic
- NEVER invent features or specs not in the data
- NEVER mention personal details unless the user provided them
- Keep the total response under 400 words
- The follow-up questions at the end are REQUIRED — never skip them"""},
```

**2. Update the concierge system prompt** (line 447) to also include follow-up questions:

Replace the existing system prompt with:
```python
{"role": "system", "content": "You are ReviewGuide, a friendly and knowledgeable AI shopping assistant. Never open with phrases like 'Based on X sources' or mention how many sources you searched. Never describe your process. Write 2-3 SHORT sentences (max 60 words) explaining WHY these products match the user's needs. Reference their criteria from the conversation (budget, features, use case). Do NOT list products — they are shown in cards below. End with 2-3 specific follow-up questions like 'Want to compare the top two?' or 'Looking for budget alternatives?' — make them relevant to the specific products shown."},
```

**3. Cap product cards at 5** — In the ui_blocks assembly section, after the loop that builds product_review cards (around line 874, after `review_card_count += 1`), add a break:

Inside the `for idx, product in enumerate(products_with_offers, 1):` loop (~line 788), add at the very top of the loop body:
```python
if review_card_count >= 5:
    break
```

Also, in the `products_by_provider` assembly loop (~line 386), change `for offer in affiliate_group["offers"][:5]:` — this already caps at 5 per group, but also cap the overall products_by_provider to 5 total products per provider:
```python
provider_products = provider_products[:5]  # after the inner loop, before the if provider_products block
```

**4. Cap the concierge product listing** — In the concierge fallback text assembly (~line 961), change `if title in seen_products or product_idx >= 8:` to `if title in seen_products or product_idx >= 5:`.

**IMPORTANT:** Do NOT modify any ui_blocks structure, render functions in Message.tsx, or streaming logic. Only modify system prompts and add the cap logic.
  </action>
  <verify>
    <automated>cd /c/Users/habib/Downloads/ReviewGuide-SourceCode && grep -c "follow-up question" backend/mcp_server/tools/product_compose.py && grep -c "review_card_count >= 5" backend/mcp_server/tools/product_compose.py && grep -c "product_idx >= 5" backend/mcp_server/tools/product_compose.py</automated>
  </verify>
  <done>product_compose blog_article prompt enforces Blog Review -> Product Cards -> Follow-up Questions format. Concierge prompt includes follow-up questions. Product cards capped at 5. Concierge product list capped at 5. No frontend changes made.</done>
</task>

</tasks>

<verification>
1. `grep -n "USE_CURATED_LINKS" backend/app/core/config.py backend/.env backend/mcp_server/tools/product_affiliate.py` — flag present in all 3 files
2. `grep -c "follow-up" backend/mcp_server/tools/product_compose.py` — follow-up instructions present in prompts
3. `grep -n "review_card_count >= 5" backend/mcp_server/tools/product_compose.py` — card cap present
4. `grep -n "product_idx >= 5" backend/mcp_server/tools/product_compose.py` — concierge list cap present
5. `grep -n "curated_amazon_links\[:5\]" backend/mcp_server/tools/product_affiliate.py` — curated results capped at 5
</verification>

<success_criteria>
- USE_CURATED_LINKS=true is set in .env and defined in config.py
- When flag is on, product_affiliate returns ONLY curated amzn.to links (no live API calls), capped at 5
- product_compose blog_article prompt explicitly requires follow-up questions at the end of every response
- product_compose concierge prompt includes follow-up question requirement
- Product review cards capped at 5 maximum per response
- Concierge product list capped at 5 maximum
- No frontend files modified
- No existing LangGraph workflow, streaming, or ui_blocks structure changed
</success_criteria>

<output>
After completion, create `.planning/quick/1-uncle-mike-response-format-and-curated-l/1-SUMMARY.md`
</output>

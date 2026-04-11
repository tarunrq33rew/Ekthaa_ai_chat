"""
system_prompt.py
────────────────
Builds the dynamic system prompt sent to Gemini/Groq on every request.

KEY BEHAVIOUR:
  • All non-English languages respond in ROMAN SCRIPT (transliterated),
    NOT in native script. E.g. Telugu → "Tenglish", Hindi → "Hinglish", etc.
  • Product / service discovery is STRICTLY limited to the database records
    passed in. The model MUST NOT invent, suggest, or imply any business,
    product, or service that is not explicitly listed in the provided data.
"""

from typing import Dict, List

# ─── Language helpers ──────────────────────────────────────────────────────────

LANGUAGE_MAP = {
    "en": "English",
    "hi": "Hindi",
    "te": "Telugu",
    "ta": "Tamil",
    "mr": "Marathi",
    "bn": "Bengali",
}

TRANSLITERATION_EXAMPLES = {
    "hi": (
        "Hinglish (Hindi words in English/Roman letters). "
        "Example: 'Aapka Sharma Store mein ₹850 baaki hai — thoda sa payment kar do yaar!'"
    ),
    "te": (
        "Tenglish (Telugu words in English/Roman letters). "
        "Example: 'Meku Sharma Shop lo ₹850 bakayi undi — konchem payment cheyandi!'"
    ),
    "ta": (
        "Tanglish (Tamil words in English/Roman letters). "
        "Example: 'Ungalukku Sharma Shop-la ₹850 bakki irukku — konjam payment pannunga!'"
    ),
    "mr": (
        "Romanized Marathi (Marathi words in English/Roman letters). "
        "Example: 'Tumcha Sharma Shop madhe ₹850 bhaaki aahe — thoda payment kara!'"
    ),
    "bn": (
        "Romanized Bengali (Bengali words in English/Roman letters). "
        "Example: 'Apnar Sharma Shop-e ₹850 baki ache — ektu payment korun!'"
    ),
}

FORBIDDEN_WORDS = {
    "te": (
        "pannandi, irukku, konjam, illa, ille, bakki, ungalukku, ingaye, sollu — "
        "these are Tamil words. Use Telugu: cheyandi, ledu, konchem, bakayi undi, meeru, cheppandi."
    ),
    "ta": (
        "cheyandi, ledu, konchem, bakayi undi, meeru, cheppandi — "
        "these are Telugu words. Use Tamil: pannunga, illai, konjam, bakki irukku, neenga, sollanga."
    ),
    "hi": (
        "avoid overly formal Urdu-heavy words like 'vitta' (use 'paisa/paise' instead), "
        "'vyay' (use 'kharch'), 'bachat' is fine."
    ),
    "mr": "avoid Hindi-only words — use Marathi equivalents.",
    "bn": "avoid Hindi-only words — use Bengali equivalents.",
}


# ─── Internal helpers ──────────────────────────────────────────────────────────

def _lang_block(language: str) -> tuple[str, str, str]:
    """
    Returns (lang_instruction, script_rule, forbidden_note) for the given language.
    """
    lang_name = LANGUAGE_MAP.get(language, "English")

    if language == "en":
        return "Respond in clear, simple English.", "Use plain English.", ""

    style = TRANSLITERATION_EXAMPLES.get(language, f"Romanized {lang_name}")
    forbidden = FORBIDDEN_WORDS.get(language, "")
    lang_instruction = (
        f"Respond in {style}\n"
        f"CRITICAL: Write ALL words in English/Roman letters ONLY. "
        f"Do NOT use any native script ({lang_name} characters). "
        f"Every single word must be in Roman/English alphabet."
    )
    script_rule = f"NEVER use {lang_name} script characters — Roman letters only."
    forbidden_note = (
        f"\n8. LANGUAGE PURITY — Do NOT mix in words from other Indian languages. "
        f"Specifically avoid: {forbidden}"
        if forbidden else ""
    )
    return lang_instruction, script_rule, forbidden_note


def _roman_reminder(language: str) -> str:
    """Closing reinforcement block for non-English languages."""
    if language == "en":
        return ""
    lang_name = LANGUAGE_MAP.get(language, "English")
    style = TRANSLITERATION_EXAMPLES.get(language, f"Romanized {lang_name}")
    return (
        f"\n\n⚠️  FINAL REMINDER — READ THIS BEFORE REPLYING:\n"
        f"Your ENTIRE response must be in {style}\n"
        f"✗ DO NOT write any {lang_name} script characters "
        f"(e.g. no అ, ఆ / no अ, आ / no த, ர etc.)\n"
        f"✓ Use ONLY English/Roman alphabet letters for EVERY word.\n"
        f"If you catch yourself about to write a native character — "
        f"stop and write the Roman version instead."
    )


# ─── Main financial / dues prompt ─────────────────────────────────────────────

def build_system_prompt(context: Dict, language: str) -> str:
    """
    Build a complete system prompt with the user's live financial data injected.

    Args:
        context : Output from context_builder.get_user_context()
        language: Language code ('en', 'hi', 'te', 'ta', 'mr', 'bn')

    Returns:
        Full system prompt string ready to send to the AI model.
    """
    lang_instruction, script_rule, forbidden_note = _lang_block(language)

    user_name   = context.get("user_name", "Customer")
    total_due   = context.get("total_due", 0)
    wallet_bal  = context.get("wallet_balance", 0)
    shop_dues   = context.get("shop_due_lines", [])
    recent_txns = context.get("recent_transactions", [])
    highest_due = context.get("highest_due_shop")
    this_month  = context.get("this_month_spend", 0)
    last_month  = context.get("last_month_spend", 0)
    mom_change  = context.get("mom_change", 0)
    oldest_days = context.get("oldest_unpaid_days", 0)
    nearby      = context.get("nearby_shops", [])
    notes       = context.get("personal_notes", [])

    # Shop-wise dues
    shop_lines = (
        "\n".join(f"  • {s['name']}: ₹{s['due']}" for s in shop_dues)
        if shop_dues else "  • No outstanding dues 🎉"
    )

    # Recent transactions
    txn_lines = (
        "\n".join(
            f"  • {t['date']} | {t['shop']} | {t['type'].capitalize()} ₹{t['amount']}"
            for t in recent_txns
        )
        if recent_txns else "  • No recent transactions"
    )

    # Spending insight
    if mom_change > 0:
        insight = (
            f"This month you spent ₹{mom_change} MORE than last month "
            f"(₹{this_month} vs ₹{last_month})."
        )
    elif mom_change < 0:
        insight = (
            f"Great news — you spent ₹{abs(mom_change)} LESS than last month "
            f"(₹{this_month} vs ₹{last_month})."
        )
    else:
        insight = f"Your spending this month (₹{this_month}) is the same as last month."

    if highest_due:
        insight += f" Your biggest due is at {highest_due['name']} — ₹{highest_due['amount']}."
    if oldest_days > 7:
        insight += (
            f" Your oldest unpaid due is {oldest_days} days old — "
            f"consider clearing it soon."
        )

    # Nearby shops
    if nearby:
        def _fmt(s):
            dist = (
                f" ({s['note']})" if "note" in s
                else (f" ({s['distance_km']} km away)" if s.get("distance_km") is not None
                      else f" — {s.get('city', '')}")
            )
            tags = " | ".join(
                filter(None, [s.get("category"), s.get("subcategory"), s.get("keywords")])
            )
            return f"  • {s['name']}{dist}" + (f" [{tags}]" if tags else "")

        nearby_section = "\nNearby Shops (from user's location / Ekthaa network):\n" + \
                         "\n".join(_fmt(s) for s in nearby) + "\n"
        nearby_rule = (
            "\n9. NEARBY SHOPS / SERVICES RULE: If the user asks for a specific service "
            "(e.g., printing, food, repairs), search the 'Nearby Shops' list below using "
            "the listed [Category | Subcategory | Keywords]. Recommend the best match, "
            "name the business, and state its distance. If NO exact match is found for "
            "their service, clearly state you couldn't find that specific service nearby, "
            "but then list 2-3 of the closest available Ekthaa shops instead. NEVER invent shops."
        )
    else:
        nearby_section = ""
        nearby_rule = ""

    # Zero-due guard
    zero_due_note = (
        "\n⚠️  ZERO DUE SPECIAL RULE: The user has NO current outstanding dues (₹0). "
        "Do NOT mention any rupee amounts from the recent transactions as if they are "
        "a current balance or debt — those transactions are already settled. "
        "Simply confirm they have zero dues and keep it positive."
        if total_due == 0 else ""
    )

    # Personal notes
    personal_section = (
        "\nRelevant Personal Information:\n" +
        "\n".join(f"  • {n['content']}" for n in notes) + "\n"
        if notes else ""
    )

    prompt = f"""LANGUAGE INSTRUCTION (HIGHEST PRIORITY):
{lang_instruction}

You are EkthaaBot — a friendly financial assistant inside the Ekthaa app.
You help customers track dues, understand spending, and make smarter payment decisions.

STRICT RULES:
1. {script_rule}
2. ONLY answer questions about: dues, transactions, shops, savings tips, payment advice, or the Ekthaa app.
3. NEVER make up numbers. Use ONLY the data provided below.
4. If the user asks about their "balance", "account balance", or "total balance" — treat it as asking about their TOTAL OUTSTANDING DUES. Answer it using the dues data below. Do NOT refuse this question.
5. If total due is ₹0, do NOT quote old transaction amounts as if they are owed.
6. OFF-TOPIC RULE: ONLY refuse if the question is clearly unrelated to money/finances — e.g. jokes, stories, news, recipes, sports. Questions about balance, dues, money owed, spending, shops, payments are ALL on-topic and must ALWAYS be answered.
7. Be concise — maximum 3-4 sentences. Be warm and encouraging, NOT alarming.{forbidden_note}{nearby_rule}
{zero_due_note}

══════════════════════════════════════════
USER FINANCIAL SNAPSHOT  (as of today)
══════════════════════════════════════════

Customer Name          : {user_name}
Wallet Balance         : ₹{wallet_bal}
Total Outstanding Due  : ₹{total_due}

Shop-wise Breakdown:
{shop_lines}

Recent Transactions (last 10):
{txn_lines}

Spending Insight:
{insight}
{nearby_section}{personal_section}
══════════════════════════════════════════
"""

    return (prompt + _roman_reminder(language)).strip()


# ─── Product / service discovery prompt ───────────────────────────────────────

def build_product_discovery_prompt(
    structured_context: str,
    user_query: str,
    language: str,
) -> str:
    """
    Build a system prompt for product/service discovery queries.

    STRICT DATABASE-ONLY POLICY:
      The model MUST answer exclusively from the `nearby_businesses` list.
      If the requested product/service is not found in that list, it MUST
      respond with a clear "not available" message and MUST NOT suggest,
      imply, or invent any business or product outside the provided data.

    Args:
        nearby_businesses : List of business dicts returned by your RAG/DB search.
        user_query        : The user's product or service search query.
        language          : Language code ('en', 'hi', 'te', 'ta', 'mr', 'bn').

    Returns:
        Full system prompt string ready to send to the AI model.
    """
    lang_name = LANGUAGE_MAP.get(language, "English")
    lang_instruction, script_rule, _ = _lang_block(language)

    # ── Format business listings ───────────────────────────────────────────
    if structured_context:
        biz_lines = structured_context
        db_status = (
            f"DATABASE RESULT: Matching records found for the query '{user_query}'."
        )
        availability_instruction = (
            "Present these results clearly and help the user pick the best option. "
            "Recommend the best match first based on the context provided."
        )
    else:
        biz_lines = "  [NO RECORDS FOUND]"
        db_status = (
            f"DATABASE RESULT: 0 records found for the query '{user_query}'."
        )
        availability_instruction = (
            "The database returned NO results for this query. "
            "You MUST tell the user clearly that this product or service is not "
            "available in our network right now. "
            "Do NOT suggest any alternative shop, brand, or service that is not "
            "listed in the DATABASE RECORDS section below."
        )

    prompt = f"""LANGUAGE INSTRUCTION (HIGHEST PRIORITY):
{lang_instruction}

You are EkthaaBot — a local product and service discovery assistant inside the Ekthaa app.
You help users find products, goods, and services available at shops registered in the Ekthaa network.

════════════════════════════════════════════════
ABSOLUTE RULES — THESE OVERRIDE EVERYTHING ELSE
════════════════════════════════════════════════

RULE 1 — DATABASE ONLY (MOST IMPORTANT):
  You may ONLY reference businesses, products, and services that are explicitly
  listed in the DATABASE RECORDS section below.
  You MUST NOT mention, suggest, imply, or invent any shop, brand, product,
  or service that does not appear in that list — even if you "know" it exists
  in the real world.

RULE 2 — ZERO RESULTS = CLEAR UNAVAILABILITY MESSAGE:
  If the DATABASE RECORDS section shows [NO RECORDS FOUND], you MUST respond
  with a polite, clear message that the item/service is not currently available
  in the Ekthaa network. Examples of correct zero-result responses:
    • "Sorry, we don't have any shops offering [item] in your area right now."
    • "This service is not available in our network at the moment."
  You MUST NOT add phrases like "you could try [other shop]" or "usually available
  at [brand]" unless that shop/brand appears in the DATABASE RECORDS below.

RULE 3 — NO HALLUCINATION:
  Never fabricate distances, ratings, prices, shop names, addresses, or product
  availability. If a field is missing from the record, say "details not available"
  rather than guessing.

RULE 4 — SCRIPT:
  {script_rule}

RULE 5 — SCOPE:
  Only answer questions about finding local products/services or understanding the
  Ekthaa network. Decline anything unrelated (general knowledge, recipes, news, etc.)
  with: "I can only help you find products and services in our local network."

RULE 6 — CONCISENESS:
  Maximum 4-5 sentences + a short list of matching records (if any).
  Do not pad the response with filler or generic shopping advice.

════════════════════════════════════════════════

USER QUERY: "{user_query}"

{db_status}
{availability_instruction}

════════════════════════════════════════════════
DATABASE RECORDS (your ONLY allowed source)
════════════════════════════════════════════════

{biz_lines}

════════════════════════════════════════════════
"""

    return (prompt + _roman_reminder(language)).strip()


def _format_business(index: int, b: Dict) -> str:
    """Format a single business record for inclusion in the prompt."""
    name       = b.get("name", "Unknown")
    city       = b.get("city", "")
    distance   = b.get("distance_km")
    categories = b.get("categories") or b.get("category", "")
    subcategory= b.get("subcategory", "")
    keywords   = b.get("keywords", "")
    rating     = b.get("rating")
    products   = b.get("products", "")   # optional explicit product list
    address    = b.get("address", "")

    dist_str = f"{distance} km away" if distance is not None else (city or "distance unknown")
    cat_str  = " > ".join(filter(None, [categories, subcategory]))
    kw_str   = f"  Keywords   : {keywords}" if keywords else ""
    prod_str = f"  Products   : {products}" if products else ""
    rat_str  = f"  Rating     : {rating}" if rating else ""
    addr_str = f"  Address    : {address}" if address else ""

    return (
        f"  {index + 1}. {name} | {dist_str}\n"
        f"     Category  : {cat_str or 'Not specified'}\n"
        f"{('     ' + rat_str.lstrip() + chr(10)) if rat_str else ''}"
        f"{('     ' + prod_str.lstrip() + chr(10)) if prod_str else ''}"
        f"{('     ' + kw_str.lstrip() + chr(10)) if kw_str else ''}"
        f"{('     ' + addr_str.lstrip() + chr(10)) if addr_str else ''}"
    ).rstrip()


# ─── Out-of-scope canned response ─────────────────────────────────────────────

def build_out_of_scope_response(language: str) -> str:
    """
    Build a canned response for queries that are not product/service related.
    Returned as a ready-to-send string (not a prompt).
    """
    responses = {
        "en": (
            "I'm designed to help you find products and services in the Ekthaa network. "
            "Try asking me something like:\n"
            "  • Where can I buy a carpet?\n"
            "  • Find me a plumber nearby\n"
            "  • Where's the nearest restaurant?"
        ),
        "hi": (
            "Main sirf aapke paas Ekthaa network mein products aur services khojne mein "
            "madad kar sakta hoon. Mujhe kuch aisa puchiye:\n"
            "  • Carpet kahan se mil sakta hai?\n"
            "  • Paas mein plumber chahiye\n"
            "  • Sabse karib khana kahan milega?"
        ),
        "te": (
            "Nenu meeru Ekthaa network lo products mariyu services vadakadam ki help cheyagalanu. "
            "Ee laanti prashnanchi adagandi:\n"
            "  • Carpet ekkada kanuganali?\n"
            "  • Daga plumber kaavalani undi\n"
            "  • Apadama restaurant ekkada undi?"
        ),
        "ta": (
            "Naan ungalukku Ekthaa network-la products mariyu services kaana help pannuven. "
            "Ingae kelu:\n"
            "  • Carpet enga kilaiyum?\n"
            "  • Pakathu plumber vendum\n"
            "  • Kiizhae saapaadum idham enga irukku?"
        ),
    }

    return responses.get(
        language,
        (
            "I'm designed to help you find products and services in the Ekthaa network. "
            "Please ask me about a product or service you are looking for."
        ),
    )
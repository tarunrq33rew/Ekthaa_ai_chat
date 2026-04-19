"""
context_builder.py
──────────────────
Fetches live user financial data from Appwrite via direct REST API calls
and returns a structured context dict injected into the AI system prompt.

Uses direct HTTP (requests) instead of the Appwrite Python SDK to avoid a
known SDK bug where queries are sent as a request body on GET endpoints.

Features:
- Per-user in-memory cache (5-minute TTL) to reduce Appwrite API calls
- Computes total_due, per-shop dues, spending insights (MoM, highest due)
"""

import os
import time
import logging
from datetime import datetime, timezone
from typing import Dict, List, Optional
from collections import defaultdict

import requests
import math
import json
from dotenv import load_dotenv

load_dotenv()

import re

logger = logging.getLogger(__name__)

# ── In-memory caches ─────────────────────────────────────────────────────────
_context_cache: Dict[str, tuple] = {}
CACHE_TTL_SECONDS = 300  # 5 minutes

_all_biz_cache: Dict[str, any] = {"data": [], "timestamp": 0}
BIZ_CACHE_TTL = 900  # 15 minutes


def _appwrite_headers() -> dict:
    """Build Appwrite REST API auth headers."""
    return {
        "Content-Type": "application/json",
        "X-Appwrite-Project": os.getenv("APPWRITE_PROJECT_ID", ""),
        "X-Appwrite-Key": os.getenv("APPWRITE_API_KEY", ""),
    }


def _appwrite_get(path: str, queries: Optional[List[str]] = None) -> dict:
    """
    Make a GET request to the Appwrite REST API.
    Passes queries as URL query parameters (not in request body).
    """
    endpoint = os.getenv("APPWRITE_ENDPOINT", "https://cloud.appwrite.io/v1")
    url = f"{endpoint}{path}"
    params = {}
    if queries:
        # Appwrite expects: queries[]=<encoded_string>&queries[]=...
        params["queries[]"] = queries

    try:
        resp = requests.get(url, headers=_appwrite_headers(), params=params, timeout=10)
        resp.raise_for_status()
        return resp.json()
    except requests.exceptions.HTTPError as e:
        if e.response.status_code == 404:
            logger.warning(f"Appwrite 404: {path} not found. Returning empty structure.")
            return {}
        raise e
    except Exception as e:
        logger.error(f"Appwrite Connectivity Error ({url}): {e}")
        return {}


def _list_documents(collection: str, queries: Optional[List[str]] = None) -> List[dict]:
    """List documents from an Appwrite collection."""
    db_id = os.getenv("APPWRITE_DB_ID", "Ekthaa_db")
    path = f"/databases/{db_id}/collections/{collection}/documents"
    try:
        result = _appwrite_get(path, queries)
        return result.get("documents", [])
    except Exception as e:
        logger.warning(f"Failed to list documents in '{collection}': {e}")
        return []


def _get_document(collection: str, doc_id: str) -> dict:
    """Get a single document from an Appwrite collection."""
    db_id = os.getenv("APPWRITE_DB_ID", "Ekthaa_db")
    path = f"/databases/{db_id}/collections/{collection}/documents/{doc_id}"
    try:
        return _appwrite_get(path)
    except Exception as e:
        logger.warning(f"Failed to get document '{doc_id}' from '{collection}': {e}")
        return {}


def _appwrite_query_equal(attribute: str, value: str) -> str:
    """Build an Appwrite equal query string."""
    import json
    return json.dumps({"method": "equal", "attribute": attribute, "values": [value]})


def _appwrite_query_limit(n: int) -> str:
    """Build an Appwrite limit query string."""
    import json
    return json.dumps({"method": "limit", "values": [n]})


# ── Data fetching ─────────────────────────────────────────────────────────────

def _fetch_raw_data(user_id: str) -> dict:
    """Fetch transactions, shops, and user profile from Appwrite.

    The app passes the Appwrite Auth user_id, but the customers collection
    uses its own $id as the primary key. Transactions are linked by customer_id
    which equals the customers.$id — NOT the auth user_id.

    Resolution order:
    1. Try fetching customer doc directly by $id (fast path: user_id == $id)
    2. If not found, query customers by user_id field to get the real $id
    """
    txn_col = os.getenv("APPWRITE_TRANSACTIONS_COLLECTION", "transactions")
    usr_col = os.getenv("APPWRITE_USERS_COLLECTION", "customers")
    biz_col = os.getenv("APPWRITE_BUSINESSES_COLLECTION", "businesses")

    # ── Step 1: resolve the customer document ─────────────────────────────
    user_doc = _get_document(usr_col, user_id)
    customer_doc_id = user_id  # optimistic

    if not user_doc.get("$id"):
        # user_id is an auth UID — query by the user_id field
        results = _list_documents(usr_col, [
            _appwrite_query_equal("user_id", user_id),
        ])
        if results:
            user_doc = results[0]
            customer_doc_id = user_doc["$id"]
            logger.info(f"Resolved auth uid {user_id[:8]}… → customer doc {customer_doc_id[:8]}…")
        else:
            logger.warning(f"No customer doc found for user_id={user_id}")

    # ── Step 2: fetch all collections where this user appears ──────────
    q_cust = _appwrite_query_equal("customer_id", customer_doc_id)

    # Transactions (purchase history)
    transactions = _list_documents(txn_col, [
        q_cust,
        _appwrite_query_limit(500),
    ])

    # Customer credits — authoritative per-shop balance ledger
    customer_credits = _list_documents("customer_credits", [
        q_cust,
        _appwrite_query_limit(100),
    ])

    # Recurring transactions (standing orders / EMIs)
    recurring = _list_documents("recurring_transactions", [
        q_cust,
        _appwrite_query_limit(50),
    ])

    # Scratch cards won by the user
    scratch_cards = _list_documents("scratch_cards", [
        q_cust,
        _appwrite_query_limit(50),
    ])

    # Collect unique shop IDs from transactions AND credits
    shop_ids = list({
        t.get("shop_id") or t.get("business_id")
        for t in (transactions + customer_credits)
        if t.get("shop_id") or t.get("business_id")
    })

    # Fetch each shop document
    shops: List[dict] = []
    for shop_id in shop_ids:
        doc = _get_document(biz_col, shop_id)
        if doc:
            shops.append(doc)

    return {
        "transactions": transactions,
        "customer_credits": customer_credits,
        "recurring": recurring,
        "scratch_cards": scratch_cards,
        "shops": shops,
        "user": user_doc,
    }


# ── Context computation ───────────────────────────────────────────────────────

def _compute_context(raw: dict, user_id: str) -> dict:
    """Derive financial summary from raw Appwrite data."""
    transactions: List[dict] = raw["transactions"]
    customer_credits: List[dict] = raw.get("customer_credits", [])
    recurring: List[dict] = raw.get("recurring", [])
    scratch_cards: List[dict] = raw.get("scratch_cards", [])
    shops: List[dict] = raw["shops"]
    user: dict = raw["user"]

    # shop_lookup: id -> {name, city}
    shop_lookup = {
        s["$id"]: {
            "name": s.get("name", "Unknown Shop"),
            "city": (s.get("city") or "").lower().strip()
        }
        for s in shops if s.get("$id")
    }

    now = datetime.now(timezone.utc)
    current_month, current_year = now.month, now.year
    prev_month = current_month - 1 if current_month > 1 else 12
    prev_year = current_year if current_month > 1 else current_year - 1

    # ── Shop dues: use customer_credits as authoritative source ─────────────
    # customer_credits.current_balance is the live, server-maintained balance.
    # Positive = customer owes shop (credit/due). Negative = shop owes customer.
    shop_dues: Dict[str, float] = {}
    if customer_credits:
        for cc in customer_credits:
            sid = cc.get("business_id", "")
            bal = float(cc.get("current_balance") or 0)
            if bal > 0 and cc.get("is_active", True):
                shop_dues[sid] = round(bal, 2)
    else:
        # Fallback: compute from transactions if no credit ledger exists
        for t in transactions:
            sid = t.get("business_id", "")
            amount = float(t.get("amount", 0))
            txn_type = (t.get("transaction_type") or t.get("type") or "").lower()
            if txn_type in ("credit", "purchase", "due"):
                shop_dues[sid] = shop_dues.get(sid, 0.0) + amount
            elif txn_type in ("payment", "repayment", "paid"):
                shop_dues[sid] = shop_dues.get(sid, 0.0) - amount
        shop_dues = {k: round(v, 2) for k, v in shop_dues.items() if v > 0}

    total_due = round(sum(shop_dues.values()), 2)

    # ── Month-over-month spend & oldest unpaid (from transactions) ───────
    this_month_spend = 0.0
    last_month_spend = 0.0
    this_month_city_spend = defaultdict(float)
    last_month_city_spend = defaultdict(float)
    oldest_unpaid_days = 0

    for t in transactions:
        amount = float(t.get("amount", 0))
        txn_type = (t.get("transaction_type") or t.get("type") or "").lower()
        is_credit = txn_type in ("credit", "purchase", "due")
        shop_id = t.get("business_id", "") or t.get("shop_id", "")
        shop_city = shop_lookup.get(shop_id, {}).get("city", "unknown")

        try:
            created_str = t.get("created_at") or t.get("$createdAt") or ""
            if created_str and is_credit:
                created_at = datetime.fromisoformat(created_str.replace("Z", "+00:00"))
                if created_at.month == current_month and created_at.year == current_year:
                    this_month_spend += amount
                    this_month_city_spend[shop_city] += amount
                elif created_at.month == prev_month and created_at.year == prev_year:
                    last_month_spend += amount
                    last_month_city_spend[shop_city] += amount
                days_old = (now - created_at).days
                if days_old > oldest_unpaid_days:
                    oldest_unpaid_days = days_old
        except Exception:
            pass

    highest_due_shop = None
    if shop_dues:
        top_sid = max(shop_dues, key=shop_dues.get)
        highest_due_shop = {
            "name": shop_lookup.get(top_sid, {}).get("name", "Unknown Shop"),
            "amount": shop_dues[top_sid],
        }

    shop_due_lines = sorted(
        [{"name": shop_lookup.get(sid, {}).get("name", f"Shop {sid[:6]}"), "due": due}
         for sid, due in shop_dues.items()],
        key=lambda x: x["due"], reverse=True
    )

    # Recent 10 transactions
    sorted_txns = sorted(
        transactions,
        key=lambda t: t.get("created_at") or t.get("$createdAt") or "",
        reverse=True
    )
    recent_transactions = [
        {
            "shop": shop_lookup.get(t.get("business_id", "") or t.get("shop_id", ""), {}).get("name", "Unknown Shop"),
            "amount": float(t.get("amount", 0)),
            "type": (t.get("transaction_type") or t.get("type") or "unknown").lower(),
            "date": (t.get("created_at") or t.get("$createdAt") or "")[:10],
        }
        for t in sorted_txns[:10]
    ]

    return {
        "user_name": user.get("name", "Customer"),
        "wallet_balance": float(user.get("wallet_balance") or 0),
        "total_due": total_due,
        "shop_due_lines": shop_due_lines,
        "recent_transactions": recent_transactions,
        "highest_due_shop": highest_due_shop,
        "this_month_spend": round(this_month_spend, 2),
        "last_month_spend": round(last_month_spend, 2),
        "mom_change": round(this_month_spend - last_month_spend, 2),
        "city_spend_current": {k: round(v, 2) for k, v in this_month_city_spend.items()},
        "city_spend_previous": {k: round(v, 2) for k, v in last_month_city_spend.items()},
        "oldest_unpaid_days": oldest_unpaid_days,
    }


# ── Nearby shops ─────────────────────────────────────────────────────

def _haversine_km(lat1: float, lng1: float, lat2: float, lng2: float) -> float:
    """Return great-circle distance in km between two GPS points."""
    R = 6371.0
    dlat = math.radians(lat2 - lat1)
    dlng = math.radians(lng2 - lng1)
    a = math.sin(dlat/2)**2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlng/2)**2
    return R * 2 * math.asin(math.sqrt(a))


def _shop_entry(biz: dict, distance_km: Optional[float]) -> dict:
    """Build a standardised shop dict from a business document."""
    kw = biz.get("keywords") or []
    keywords_str = ", ".join(kw) if isinstance(kw, list) else str(kw)
    return {
        "name": biz.get("name", "Unknown Shop"),
        "city": biz.get("city", ""),
        "category": biz.get("category") or biz.get("business_type") or "",
        "subcategory": biz.get("subcategory") or "",
        "keywords": keywords_str,
        "distance_km": distance_km,
        "phone": biz.get("phone_number") or biz.get("phone") or "",
    }


def _get_all_businesses() -> List[dict]:
    """Fetch all Appwrite businesses up to 1000 and cache globally for 15 mins."""
    global _all_biz_cache
    if time.time() - _all_biz_cache["timestamp"] < BIZ_CACHE_TTL and _all_biz_cache["data"]:
        return _all_biz_cache["data"]

    biz_col = os.getenv("APPWRITE_BUSINESSES_COLLECTION", "businesses")
    all_biz = []
    offset = 0
    while True:
        q_limit = _appwrite_query_limit(100)
        q_offset = json.dumps({"method": "offset", "values": [offset]})
        batch = _list_documents(biz_col, [q_limit, q_offset])
        if not batch:
            break
        all_biz.extend(batch)
        offset += len(batch)
        if len(batch) < 100 or offset >= 1000:
            break

    _all_biz_cache["data"] = all_biz
    _all_biz_cache["timestamp"] = time.time()
    return all_biz


def get_nearby_shops(
    lat: Optional[float] = None,
    lng: Optional[float] = None,
    city: Optional[str] = None,
    query: Optional[str] = None,
    radius_km: float = 10.0,
    limit: int = 15,
) -> List[dict]:
    """
    Return relevant businesses from the Ekthaa directory.
    If 'query' is provided, it extracts keywords and scores all businesses
    (giving priority to exact matches anywhere in Ekthaa).
    Then pads with GPS radius and city fallbacks.
    """
    from services.rag_service import search_businesses
    
    all_biz = _get_all_businesses()

    # 1. RAG Semantic Search
    rag_matches = []
    if query:
        # returns [{"id": biz_id, "name": n, "city": c, "score": float}]
        rag_matches = search_businesses(query, top_k=5)
        
    # Build a lookup for RAG scores
    rag_scores = {m["id"]: m["score"] for m in rag_matches}

    scored_shops = []
    for biz in all_biz:
        biz_id = biz.get("$id")
        score = rag_scores.get(biz_id, 0.0)

        blat = biz.get("latitude")
        blng = biz.get("longitude")
        dist = None
        if lat is not None and lng is not None and blat and blng:
            try:
                dist = _haversine_km(lat, lng, float(blat), float(blng))
            except (ValueError, TypeError):
                pass
        scored_shops.append({"score": score, "dist": dist, "biz": biz})

    merged_results = []
    seen = set()

    def _add(biz, dist=None, note=None):
        k = biz.get("name", "").lower()
        if k not in seen:
            seen.add(k)
            entry = _shop_entry(biz, round(dist, 2) if dist else None)
            if note: entry["note"] = note
            merged_results.append(entry)

    # 1. Semantic Matches (RAG) (anywhere in Ekthaa)
    if rag_matches:
        matches = [s for s in scored_shops if s["score"] > 0]
        # Sort by score desc, then distance asc
        matches.sort(key=lambda x: (-x["score"], x["dist"] if x["dist"] is not None else 9999))
        for m in matches[:5]:
            d_str = f"{round(m['dist'],1)}km" if m['dist'] is not None else "Ekthaa Network"
            _add(m["biz"], m["dist"], f"Semantic Match • {d_str}")

    # 2. GPS Radius Mode
    if lat is not None and lng is not None:
        gps_list = [s for s in scored_shops if s["dist"] is not None]
        gps_list.sort(key=lambda x: x["dist"])
        
        in_range = [s for s in gps_list if s["dist"] <= radius_km]
        for s in in_range:
            _add(s["biz"], s["dist"])

        # If we have very few matches, append closest regardless of radius
        if len(merged_results) < 3:
            beyond = [s for s in gps_list if s["dist"] > radius_km]
            for s in beyond[:max(0, 8 - len(merged_results))]:
                _add(s["biz"], s["dist"], f"~{round(s['dist'],1)}km (wider search)")

    # 3. City Fallback
    if city:
        city_lower = city.lower().strip()
        for s in scored_shops:
            if (s["biz"].get("city") or "").lower().strip() == city_lower:
                _add(s["biz"], s["dist"])

    # 4. Absolute Fallback
    if not merged_results:
        for s in scored_shops[:limit]:
            _add(s["biz"], s["dist"])

    logger.info(f"📍 Ekthaa shops: {len(merged_results[:limit])} (query: {query})")
    return merged_results[:limit]

# ── Public API ─────────────────────────────────────────────────────

def get_user_context(
    user_id: str,
    lat: Optional[float] = None,
    lng: Optional[float] = None,
    query: Optional[str] = None,
) -> dict:
    """
    Returns the financial context for a user.
    Uses 5-minute in-memory cache to minimise Appwrite calls.
    Nearby shops are dynamically injected based on lat/lng/query.
    """
    lat_bucket = round(lat, 2) if lat else None
    lng_bucket = round(lng, 2) if lng else None
    cache_key = f"{user_id}|{lat_bucket}|{lng_bucket}"

    if cache_key in _context_cache:
        cached_ctx, cached_ts = _context_cache[cache_key]
        if time.time() - cached_ts < CACHE_TTL_SECONDS:
            logger.info(f"📦 Cache hit for {cache_key[:20]}")
            ctx = dict(cached_ctx)
            user_city = ctx.get("user_city", "")
            ctx["nearby_shops"] = get_nearby_shops(lat=lat, lng=lng, city=user_city, query=query)
            ctx["personal_notes"] = []
                
            return ctx

    logger.info(f"🔄 Fetching fresh context for user {user_id}")
    raw = _fetch_raw_data(user_id)
    ctx = _compute_context(raw, user_id)

    # Store city for future cache hits
    user_city = raw["user"].get("city") or raw["user"].get("state", "")
    ctx["user_city"] = user_city

    # Cache only the financial + profile data
    _context_cache[cache_key] = (dict(ctx), time.time())

    # Attach dynamic nearby shops per-query before returning
    ctx["nearby_shops"] = get_nearby_shops(lat=lat, lng=lng, city=user_city, query=query)
    ctx["personal_notes"] = []
        
    logger.info(
        f"✅ Context built for {user_id}: total_due=₹{ctx['total_due']}, "
        f"shops={len(ctx['shop_due_lines'])}, nearby={len(ctx['nearby_shops'])}"
    )
    return ctx


def invalidate_cache(user_id: str) -> None:
    """Force-clear the cache for a user (call after a payment is recorded)."""
    _context_cache.pop(user_id, None)

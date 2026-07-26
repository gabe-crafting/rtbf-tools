# -*- coding: utf-8 -*-
"""
Shared helpers for scraping public Substack data.

Only public, unauthenticated endpoints are used:
  search   https://substack.com/api/v1/top/search?query=<q>&searchCursor=<c>
  profile  https://substack.com/api/v1/user/<handle>/public_profile
  archive  https://<pub>/api/v1/archive?sort=new&limit=<n>&offset=<n>

No endpoint exposes view counts or lets you sort an archive by engagement,
so "most engaged" is always computed over a recent-post window (see
fetch_posts / rank_posts).
"""

import io
import json
import re
import sys
import time
import unicodedata
import urllib.error
import urllib.parse
import urllib.request

UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120 Safari/537.36"
API = "https://substack.com/api/v1"


# ---------------------------------------------------------------- utilities

def eprint(*a):
    """Print progress to stderr so stdout stays clean for piping."""
    msg = " ".join(str(x) for x in a)
    try:
        print(msg, file=sys.stderr, flush=True)
    except UnicodeEncodeError:                      # narrow Windows consoles
        print(msg.encode("ascii", "replace").decode(), file=sys.stderr, flush=True)


def slugify(text):
    """'Heart Health!' -> 'heart-health'  (safe for CSS classes / data attrs)."""
    text = unicodedata.normalize("NFKD", str(text or ""))
    text = text.encode("ascii", "ignore").decode()
    text = re.sub(r"[^a-zA-Z0-9]+", "-", text).strip("-").lower()
    return text or "tag"


def load_json(path, default=None):
    try:
        with io.open(path, encoding="utf-8") as f:
            return json.load(f)
    except (IOError, OSError, ValueError):
        return default


def save_json(path, obj):
    with io.open(path, "w", encoding="utf-8") as f:
        json.dump(obj, f, ensure_ascii=False, indent=2)


# ------------------------------------------------------------------- http

def http_json(url, retries=3, timeout=45, backoff=1.6):
    """GET JSON with retries. Returns None on persistent failure (never raises)."""
    delay = 1.0
    for attempt in range(retries):
        req = urllib.request.Request(
            url, headers={"User-Agent": UA, "Accept": "application/json"})
        try:
            with urllib.request.urlopen(req, timeout=timeout) as r:
                return json.loads(r.read().decode("utf-8", "replace"))
        except urllib.error.HTTPError as e:
            # 404 = genuinely absent; don't burn retries on it.
            if e.code in (404, 403):
                return None
            if attempt == retries - 1:
                eprint("    ! HTTP %s %s" % (e.code, url[:90]))
        except Exception as e:
            if attempt == retries - 1:
                eprint("    ! %s %s" % (type(e).__name__, url[:90]))
        time.sleep(delay)
        delay *= backoff
    return None


# ----------------------------------------------------------------- search

def search_accounts(query, pages=4, sleep=0.4):
    """
    Search Substack for `query`; return {handle: True} for every account that
    appears as a profile hit, a post author, or a comment author.

    Substack's search mixes result types into one `items` array and paginates
    with an opaque `nextCursor`.
    """
    found = {}
    cursor = None
    for page in range(pages):
        url = "%s/top/search?query=%s&fromSuggestedSearch=false" % (
            API, urllib.parse.quote(query))
        if cursor:
            url += "&searchCursor=" + urllib.parse.quote(cursor)

        payload = http_json(url)
        if not payload:
            break

        for item in payload.get("items", []):
            kind = item.get("type")
            if kind == "profileSearchResults":
                for prof in item.get("results", []) or []:
                    if prof.get("handle"):
                        found[prof["handle"]] = True
            elif kind in ("post", "comment"):
                for user in (item.get("context") or {}).get("users", []) or []:
                    if user.get("handle"):
                        found[user["handle"]] = True
                for byline in (item.get("post") or {}).get("publishedBylines", []) or []:
                    if byline.get("handle"):
                        found[byline["handle"]] = True

        cursor = payload.get("nextCursor")
        eprint("    page %d/%d -> %d handles" % (page + 1, pages, len(found)))
        if not cursor:
            break
        time.sleep(sleep)
    return found


# ---------------------------------------------------------------- profiles

def _primary_publication(profile):
    pubs = profile.get("publicationUsers") or []
    for pu in pubs:
        if pu.get("is_primary") and pu.get("publication"):
            return pu["publication"]
    for pu in pubs:
        if pu.get("publication"):
            return pu["publication"]
    return None


def fetch_profile(handle):
    """Return a normalised account record, or None if the profile is gone."""
    profile = http_json("%s/user/%s/public_profile" % (API, urllib.parse.quote(handle)))
    if not profile:
        return None

    pub = _primary_publication(profile)
    subdomain = (pub or {}).get("subdomain")

    return {
        "name": profile.get("name") or handle,
        "handle": handle,
        "profile_url": "https://substack.com/@%s" % handle,
        "bio": (profile.get("bio") or "").strip(),
        "followers": profile.get("followerCount") or 0,
        "subscribers_number": profile.get("subscriberCountNumber") or 0,
        "subscribers_label": profile.get("subscriberCountString") or "",
        "bestseller_tier": profile.get("bestseller_tier") or 0,
        "publication": (pub or {}).get("name"),
        "publication_url": ("https://%s.substack.com" % subdomain) if subdomain else None,
        # Publication creation date: the closest public proxy for "first post".
        # Substack exposes no reliable first-post date (the archive cannot sort
        # ascending, and sitemaps are truncated for large publications).
        "started": (pub or {}).get("created_at") or profile.get("profile_set_up_at"),
        "keywords": [],
    }


# ------------------------------------------------------------------- posts

def fetch_posts(publication_url, want=60, page_size=12, sleep=0.15):
    """
    Newest-first posts for a publication. `page_size` must stay small — large
    limits make Substack ignore `offset` and replay the first page.
    """
    if not publication_url:
        return []

    posts, seen = [], set()
    for offset in range(0, want, page_size):
        batch = http_json("%s/api/v1/archive?sort=new&limit=%d&offset=%d"
                          % (publication_url, page_size, offset))
        if not batch:
            break

        for p in batch:
            url = p.get("canonical_url")
            if not url or url in seen:
                continue
            seen.add(url)

            reactions = p.get("reaction_count") or 0
            comments = p.get("comment_count") or 0
            restacks = p.get("restacks") or 0
            posts.append({
                "title": p.get("title") or "(untitled)",
                "url": url,
                "date": p.get("post_date"),
                "reactions": reactions,
                "comments": comments,
                "restacks": restacks,
                "engagement": reactions + comments + restacks,
                "audience": p.get("audience"),
            })

        if len(batch) < page_size:      # reached the end of the archive
            break
        time.sleep(sleep)
    return posts


def rank_posts(posts, top_n=8):
    """Return (most_recent, most_engaged) slices of the same post pool."""
    recent = sorted(posts, key=lambda p: p.get("date") or "", reverse=True)[:top_n]
    engaged = sorted(posts, key=lambda p: p.get("engagement", 0), reverse=True)[:top_n]
    return recent, engaged

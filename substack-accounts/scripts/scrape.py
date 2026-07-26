# -*- coding: utf-8 -*-
"""
Collect Substack accounts by search tag and/or explicit handle, then enrich
each with profile stats and a window of recent posts.

Examples
--------
  # two tags, default depth
  python scrape.py --tag beef --tag cardiology --out ../substack_accounts.json

  # add specific people regardless of search
  python scrape.py -t "heart health" -H erictopol -H johnmandrola -o data.json

  # deeper crawl, bigger post window, only sizeable accounts
  python scrape.py -t nutrition --pages 8 --posts 120 --min-followers 5000 -o data.json

  # refresh stats but keep the existing roster (no new searching)
  python scrape.py --refresh --no-search -o data.json

Re-running is incremental by default: existing accounts keep their posts and
are not refetched unless --refresh is passed. Tags always accumulate, so you
can add a tag later without losing earlier ones.
"""

import argparse
import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from substack_lib import (eprint, fetch_posts, fetch_profile, load_json,
                          rank_posts, save_json, search_accounts)


def parse_args():
    ap = argparse.ArgumentParser(
        description="Scrape public Substack accounts by tag and/or handle.",
        formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("-t", "--tag", action="append", default=[], metavar="TERM",
                    help="search term; repeat for multiple (e.g. -t beef -t cardiology)")
    ap.add_argument("-H", "--handle", action="append", default=[], metavar="HANDLE",
                    help="explicit Substack handle to include; repeat as needed")
    ap.add_argument("-o", "--out", default="substack_accounts.json",
                    help="output JSON path (default: substack_accounts.json)")
    ap.add_argument("--pages", type=int, default=4,
                    help="search pages per tag, ~20 results each (default: 4)")
    ap.add_argument("--posts", type=int, default=60,
                    help="posts to scan per account, 0 to skip (default: 60)")
    ap.add_argument("--top", type=int, default=8,
                    help="entries in each recent/engaged list (default: 8)")
    ap.add_argument("--min-followers", type=int, default=0,
                    help="drop accounts below this follower count (default: 0)")
    ap.add_argument("--refresh", action="store_true",
                    help="refetch profiles and posts for accounts already present")
    ap.add_argument("--no-search", action="store_true",
                    help="skip searching; only refresh/handle-add into existing file")
    ap.add_argument("--handle-tag", default="manual", metavar="LABEL",
                    help="keyword applied to --handle accounts (default: manual)")
    ap.add_argument("--sleep", type=float, default=0.25,
                    help="pause between API calls in seconds (default: 0.25)")
    return ap.parse_args()


def main():
    args = parse_args()
    if not args.tag and not args.handle and not args.refresh:
        eprint("Nothing to do: pass at least one --tag or --handle, or use --refresh.")
        return 1

    existing = load_json(args.out, default={}) or {}
    accounts = {a["handle"]: a for a in existing.get("accounts", [])}
    eprint("Loaded %d existing account(s) from %s" % (len(accounts), args.out))

    if args.refresh and not accounts:
        eprint("--refresh needs an existing dataset; %s has no accounts." % args.out)
        return 1

    # ---- 1. discover handles -> {handle: [tags]} -------------------------
    discovered = {}
    if not args.no_search:
        for tag in args.tag:
            eprint("Searching %r ..." % tag)
            for handle in search_accounts(tag, pages=args.pages, sleep=args.sleep):
                discovered.setdefault(handle, []).append(tag)
    for handle in args.handle:
        discovered.setdefault(handle.lstrip("@"), []).append(args.handle_tag)
    if args.refresh:
        # Re-profile everyone already on file, keeping their existing tags.
        for handle, acct in accounts.items():
            discovered.setdefault(handle, list(acct.get("keywords", [])))

    eprint("Discovered %d unique handle(s)" % len(discovered))

    # ---- 2. profiles ------------------------------------------------------
    for i, (handle, tags) in enumerate(sorted(discovered.items()), 1):
        known = accounts.get(handle)
        if known and not args.refresh:
            for tag in tags:                       # tags accumulate, never reset
                if tag not in known["keywords"]:
                    known["keywords"].append(tag)
                    known["keywords"].sort()
            continue

        record = fetch_profile(handle)
        if not record:
            eprint("  [%d/%d] %-24s -- profile unavailable, skipped"
                   % (i, len(discovered), handle[:24]))
            continue

        if known:                                  # refresh: keep post data
            record["keywords"] = sorted(set(known["keywords"]) | set(tags))
            for key in ("recent_posts", "top_posts", "post_pool"):
                if key in known:
                    record[key] = known[key]
        else:
            record["keywords"] = sorted(set(tags))

        accounts[handle] = record
        eprint("  [%d/%d] %-24s %8d followers"
               % (i, len(discovered), (record["name"] or "")[:24], record["followers"]))
        time.sleep(args.sleep)

    # ---- 3. follower floor -----------------------------------------------
    if args.min_followers:
        before = len(accounts)
        accounts = {h: a for h, a in accounts.items()
                    if a["followers"] >= args.min_followers}
        eprint("Follower floor %d: dropped %d account(s)"
               % (args.min_followers, before - len(accounts)))

    # ---- 4. posts ---------------------------------------------------------
    if args.posts > 0:
        targets = [a for a in accounts.values()
                   if args.refresh or a.get("recent_posts") is None]
        eprint("Fetching posts for %d account(s) ..." % len(targets))
        for i, acct in enumerate(sorted(targets, key=lambda a: -a["followers"]), 1):
            pool = fetch_posts(acct.get("publication_url"), want=args.posts)
            recent, engaged = rank_posts(pool, top_n=args.top)
            acct["recent_posts"] = recent
            acct["top_posts"] = engaged
            acct["post_pool"] = len(pool)
            eprint("  [%d/%d] %-24s pool=%3d  top=%s"
                   % (i, len(targets), (acct["name"] or "")[:24], len(pool),
                      engaged[0]["engagement"] if engaged else 0))
            time.sleep(args.sleep)

    # ---- 5. save ----------------------------------------------------------
    ordered = sorted(accounts.values(), key=lambda a: a["followers"], reverse=True)
    all_tags = sorted({t for a in ordered for t in a["keywords"]})
    save_json(args.out, {
        "generated": time.strftime("%Y-%m-%d"),
        "queries": all_tags,
        "count": len(ordered),
        "accounts": ordered,
    })

    eprint("\nWrote %d account(s) to %s" % (len(ordered), args.out))
    eprint("Tags: %s" % ", ".join(all_tags))
    for a in ordered[:10]:
        eprint("  %8d  %-26s %s" % (a["followers"], (a["name"] or "")[:26],
                                    ",".join(a["keywords"])))
    return 0


if __name__ == "__main__":
    sys.exit(main())

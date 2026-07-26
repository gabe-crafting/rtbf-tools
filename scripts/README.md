# Substack directory toolkit

Three composable scripts: **scrape** public Substack accounts by tag or handle,
**build** a searchable static page from the result, **deploy** it to GitHub Pages.

Python 3.7+, standard library only. No API key, no dependencies, no login.

```
scrape.py  --tag/--handle  ->  data.json  ->  build_page.py  ->  index.html  ->  deploy.sh
```

---

## 1. scrape.py — collect accounts

```bash
# the original run that produced this site
python scrape.py --tag beef --tag cardiology --out ../substack_accounts.json

# any tags you like, plus specific people by handle
python scrape.py -t "heart health" -t nutrition -H erictopol -H johnmandrola -o data.json

# go deeper and only keep sizeable accounts
python scrape.py -t cycling --pages 8 --posts 120 --min-followers 5000 -o data.json

# refresh follower counts + posts for everyone already in the file
python scrape.py --refresh --no-search -o data.json
```

| Flag | Default | Meaning |
|---|---|---|
| `-t, --tag` | – | Search term; repeat for multiple |
| `-H, --handle` | – | Explicit handle to include; repeat for multiple |
| `-o, --out` | `substack_accounts.json` | Output path |
| `--pages` | `4` | Search pages per tag (~20 results each) |
| `--posts` | `60` | Posts scanned per account (`0` skips posts) |
| `--top` | `8` | Entries in each recent/engaged list |
| `--min-followers` | `0` | Drop accounts below this count |
| `--refresh` | off | Refetch accounts already in the file |
| `--no-search` | off | Skip searching (refresh-only runs) |
| `--handle-tag` | `manual` | Keyword applied to `--handle` accounts |
| `--sleep` | `0.25` | Pause between API calls |

**Re-running is incremental.** Existing accounts keep their posts and aren't
refetched unless `--refresh` is passed, and tags accumulate — so adding a tag
later never discards earlier ones. Progress goes to stderr, so `2>/dev/null`
silences it.

## 2. build_page.py — render the page

```bash
python build_page.py --data ../substack_accounts.json --out ../index.html
python build_page.py -d data.json -o site/index.html --title "Health Substacks"
```

Handles any number of tags, assigning each its own colour and filter chip from a
10-colour palette. The dataset is embedded in the HTML, so the page works
offline, over `file://`, and on any static host — no server, no fetch calls.

The page gives you: text search over name/publication/bio, per-tag filter chips,
sorting by followers/subscribers/start-date/name (click a column header too), a
minimum-followers slider, and a per-account accordion of most-recent and
most-engaged posts.

Every post carries two access markers, because Substack sets them separately:

- 🔒 next to the title — the post is **paid-only to read**
- a comment pill — **free** (anyone), **subs** (free or paid subscribers),
  **paid** (paid subscribers only), or **off** (comments closed)

## 3. deploy.sh — publish

```bash
./deploy.sh                          # commit, push, enable Pages if needed
./deploy.sh -m "refresh data"        # custom commit message
./deploy.sh -b main --no-pages       # just commit and push
```

Infers `owner/repo` and branch from the git remote, reads the GitHub token from
git's credential helper (never prints or stores it), enables Pages if it isn't
already on, waits for the build, and prints the live URL.

> Pages on a free account requires a **public** repository, which makes the site
> world-readable. The script warns and asks before enabling Pages on a private repo.

---

## Data shape

```jsonc
{
  "generated": "2026-07-26",
  "queries": ["beef", "cardiology"],
  "count": 39,
  "accounts": [
    {
      "name": "Eric Topol",
      "handle": "erictopol",
      "profile_url": "https://substack.com/@erictopol",
      "bio": "physician-scientist, author, editor",
      "followers": 299926,
      "subscribers_number": 212000,
      "subscribers_label": "212K+ subscribers",
      "bestseller_tier": 1000,
      "publication": "Ground Truths",
      "publication_url": "https://erictopol.substack.com",
      "started": "2021-11-30T18:05:56.883Z",
      "keywords": ["cardiology"],
      "post_pool": 60,                 // posts scanned for the ranking below
      "recent_posts": [ /* newest first */ ],
      "top_posts":    [ /* most engaged first */ ]
    }
  ]
}
```

Each post: `title`, `url`, `date`, `reactions`, `comments`, `restacks`,
`engagement` (their sum), plus two independent access fields:

| Field | Values | Meaning |
|---|---|---|
| `audience` | `everyone`, `only_paid`, … | who can **read** the post |
| `comment_access` | `everyone`, `subscribers`, `paid`, `none` | who can **comment** |
| `comment_access_raw` | Substack's original string | unnormalised, for auditing |

**These two are independent** — in the current dataset 87 free-to-read posts
allow only paid subscribers to comment, and 34 paid posts let anyone comment.
`comment_access` is normalised from Substack's `write_comment_permissions`
(`only_paid` → `paid`); unrecognised values pass through verbatim rather than
being dropped, so a new Substack value shows up as a visible label.

## Endpoints used

All public and unauthenticated:

| Purpose | Endpoint |
|---|---|
| Search | `substack.com/api/v1/top/search?query=<q>&searchCursor=<cursor>` |
| Profile | `substack.com/api/v1/user/<handle>/public_profile` |
| Archive | `<publication>/api/v1/archive?sort=new&limit=<n>&offset=<n>` |

## Caveats worth knowing

These are limits of Substack's public API, not of the scripts:

- **"Most engaged" is windowed, not all-time.** The archive can't be sorted by
  engagement, so ranking happens within the `--posts` most recent. Raise
  `--posts` for a wider window at the cost of a slower run.
- **"Started" is the publication's creation date**, the closest public proxy for
  a first post. There's no reliable first-post date: the archive can't sort
  ascending and sitemaps are truncated for large publications.
- **No view counts.** `reactions + comments + restacks` are the only public
  engagement signals.
- **Keep `page_size` small when paging the archive.** Above ~12, Substack starts
  ignoring `offset` and replays the first page. `fetch_posts` already handles this.
- **Tags reflect what search surfaced**, not editorial focus — an account can
  match `beef` from a single passing mention.
- **Be polite.** Defaults are already rate-limited; lower `--sleep` at your own risk.

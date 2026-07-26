# Substack Accounts - Beef & Cardiology

A searchable directory of large Substack accounts surfaced by searching Substack
for **beef** and **cardiology**, with each account's most-recent and most-engaged posts.

**Live page:** https://gabe-crafting.github.io/rtbf-tools/

## Contents

| Path | What it is |
|---|---|
| `index.html` | The standalone page (data embedded, no server needed) |
| `substack_accounts.json` | The raw dataset |
| `scripts/` | Reusable toolkit that generated all of the above |

## Regenerating / reusing

The `scripts/` folder is a general-purpose toolkit - it works with any tags or
handles, not just these two. Python 3.7+, standard library only, no API key.

```bash
cd scripts
python scrape.py --tag beef --tag cardiology --out ../substack_accounts.json
python build_page.py --data ../substack_accounts.json --out ../index.html
./deploy.sh
```

See [scripts/README.md](scripts/README.md) for all options and caveats.

## About the data

Follower and subscriber counts come from each account's public Substack profile.
"Started" is the date the account's publication was created - the closest public
proxy for a first post. For each account, posts are drawn from up to its ~60 most
recent, and "most engaged" means reactions + comments + restacks *within that
window*, not all-time. Keywords reflect which search term surfaced the account.

Data pulled 2026-07-26.

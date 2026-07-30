# Fight to Repair - Followers

The publicly listed followers of
[substack.com/@fighttorepair](https://substack.com/@fighttorepair), each with
the day they last **liked** or **replied to** anything on Substack. Search by
name, handle, bio, or publication; filter by activity recency and kind; every
row links to the follower's Substack profile.

**Live page:** https://gabe-crafting.github.io/rtbf-tools/fighttorepair-followers/

One of the tools in [rtbf-tools](../README.md).

## Contents

| Path | What it is |
|---|---|
| `index.html` | The standalone page (data embedded, no server needed) |
| `followers.json` | The raw dataset |
| `scripts/scrape.js` | Scrapes Substack's public API into `followers.json` |
| `scripts/build_page.js` | Embeds `followers.json` into `index.html` |

## Regenerating

Node 18+ and a `curl` binary on PATH (ships with Windows 10+, macOS, Linux),
no dependencies. Works for any profile handle, not just fighttorepair:

```bash
cd scripts
node scrape.js                       # ~2 min, 1 request per follower
node build_page.js
node scrape.js --handle someoneelse --out other.json   # any other profile
```

## How it works / caveats

Three public, unauthenticated Substack endpoints:

- `user/<handle>/public_profile` - profile id and total follower count
- `user/<id>/subscriber-lists?lists=followers` - the follower list.
  **Substack only exposes a few hundred followers publicly** (211 of 1,760 at
  scrape time); the rest are not retrievable without being logged in as the
  profile owner.
- `reader/feed/profile/<id>?types[]=like&types[]=replies` - each follower's
  public activity feed, newest first. The first item is their latest like or
  reply; its timestamp is the "last active" day shown. Users who have never
  publicly liked or replied show as "no public activity".

Requests are made through `curl` because Cloudflare challenges Node's
built-in `fetch` on the follower-list endpoint.

Data scraped 2026-07-30.

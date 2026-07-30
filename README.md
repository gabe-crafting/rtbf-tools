# RTBF Tools

A collection of small, standalone research tools. Each one is a static site with
its data baked in - no server, no build step to view, no API keys.

**Live index:** https://gabe-crafting.github.io/rtbf-tools/

## Tools

| Tool | What it is | Live |
|---|---|---|
| [`substack-accounts/`](substack-accounts/) | Searchable directory of 39 large Substack accounts surfaced by searching for **beef** and **cardiology**, with each account's most-recent and most-engaged posts | [open](https://gabe-crafting.github.io/rtbf-tools/substack-accounts/) |
| [`romanian-western-companies/`](romanian-western-companies/) | Research shortlist of 43 active Romanian SRLs with public evidence of Western ownership or leadership, filterable by nationality and headcount | [open](https://gabe-crafting.github.io/rtbf-tools/romanian-western-companies/) |
| [`ev-donor-cars/`](ev-donor-cars/) | Searchable list of all 665 donor cars on evbreakers.com by name, engine code, and battery capacity, each linking to its parts page | [open](https://gabe-crafting.github.io/rtbf-tools/ev-donor-cars/) |
| [`fighttorepair-followers/`](fighttorepair-followers/) | The 211 publicly listed followers of Substack's @fighttorepair, each with the day they last liked or replied to anything | [open](https://gabe-crafting.github.io/rtbf-tools/fighttorepair-followers/) |

Each folder is self-contained: its own `index.html`, its own dataset, its own
build scripts, and its own README explaining how to regenerate it.

## Layout

```
index.html                     # the tools index (this repo's landing page)
.nojekyll                      # serve files as-is, no Jekyll processing
substack-accounts/             # Python toolkit -> scrape.py, build_page.py
romanian-western-companies/    # Node script -> scripts/build-data.mjs
ev-donor-cars/                 # Node scripts -> scrape.js, build_page.js
fighttorepair-followers/       # Node scripts -> scrape.js, build_page.js
```

## Adding a tool

1. Create a folder with an `index.html` that works when opened directly.
2. Keep every asset path relative so it works under the `/rtbf-tools/<folder>/` prefix.
3. Add a card to the root `index.html` and a row to the table above.

## Deploying

Pages serves this repo from the `master` branch root, so pushing publishes.
`substack-accounts/scripts/deploy.sh` commits, pushes, and enables Pages if it
isn't on yet.

The Romanian SRL project arrived here from its own repository, which deployed via
a GitHub Actions workflow. That workflow was dropped in the merge because
Actions-based Pages would conflict with this repo's branch-based source; restore
it at `.github/workflows/` only if you also switch the Pages source to
"GitHub Actions".

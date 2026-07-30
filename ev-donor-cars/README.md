# EV Donor Cars

A searchable list of every donor car on
[evbreakers.com/donor-cars](https://evbreakers.com/donor-cars) — search by
name, engine code, or battery capacity; filter by make, engine, battery, and
year. Each card links to the car's parts page on evbreakers.

**Live page:** https://gabe-crafting.github.io/rtbf-tools/ev-donor-cars/

One of the tools in [rtbf-tools](../README.md).

## Contents

| Path | What it is |
|---|---|
| `index.html` | The standalone page (data embedded, no server needed) |
| `cars.json` | The raw dataset |
| `scripts/scrape.js` | Scrapes evbreakers.com into `cars.json` |
| `scripts/build_page.js` | Embeds `cars.json` into `index.html` |

## Regenerating

Node 18+ (uses built-in `fetch`), no dependencies:

```bash
cd scripts
node scrape.js        # walks all listing pages -> ../cars.json
node build_page.js    # embeds cars.json into ../index.html
```

The listing paginates via an AJAX POST to `donor-cars` with a `page` form
field; `scrape.js` walks pages until one adds no new cars, so it keeps working
if the site grows past its current page count.

## About the data

Per car: name (year + make + model as titled on the site), engine code,
variant/body style, body color, battery capacity, and the link + photo from
evbreakers. Makes are normalised (VW → VOLKSWAGEN, ŠKODA → SKODA, etc.).

**Battery capacity caveat:** evbreakers only states a kWh figure for some cars
(66 of 665 at scrape time), inside the engine string (e.g. `EM57 62KWH`) or
the title. The page's "Listed only" battery filter shows just those; everything
else has no battery data on the listing, and the per-car parts pages don't add
any.

All data belongs to evbreakers.com. Data scraped 2026-07-30 — 665 cars.

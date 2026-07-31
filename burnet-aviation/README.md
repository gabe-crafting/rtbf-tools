# Aviation Companies - Burnet, TX

A hand-researched roster of the aviation companies and organizations based at
or serving Burnet Municipal Airport / Kate Craddock Field (KBMQ) in Burnet,
TX 78611: name, phone, products/services summary, website, and address, with
sources on every card. Searchable by name/services/phone, filterable by type.

**Live page:** https://gabe-crafting.github.io/rtbf-tools/burnet-aviation/

One of the tools in [rtbf-tools](../README.md).

## Contents

| Path | What it is |
|---|---|
| `index.html` | The standalone page (data embedded, no server needed) |
| `companies.json` | The dataset, with per-company source URLs |
| `scripts/build_page.js` | Embeds `companies.json` into `index.html` |

## Updating

This dataset is hand-researched (no scraper - the sources are scattered
directories, company sites, and FAA records). Edit `companies.json`, then:

```bash
cd scripts
node build_page.js
```

## About the data

12 entries researched 2026-07-31, drawn from AirNav, FlightAware, Business Air
News, FlightSchoolList, the FAA repair-station database (via airresearch.com),
chamber/Yellow Pages listings, and each company's own site. Notes:

- **Crosby Flying Services** is the current FBO and airport manager;
  **Faulkner's Air Shop** (marked *legacy*) was the longtime FBO whose role
  Crosby took over - stale directory listings still carry it, and its old
  number now reaches Crosby.
- **C3 Air** and **C3 Airworks** are the flight-school and maintenance arms of
  one operation at 3202 S. Water St, kept on a single card with both numbers.
- **Texas Flight School** and **Aircraft Simulator Training** are sister
  operations sharing 3242 S. Water St and one phone number.
- **A Detailed Flight** (marked *unverified*) is listed at KBMQ on FlightAware
  but its website was offline at research time. **TravelTech** (marked
  *nearby*) is an off-field shop AirNav lists on the KBMQ page.
- The **City of Burnet** entry is the airport operator itself, included for
  completeness.

### On coverage

Web search alone missed several real tenants - C3 Air and ProMark Aviation
never surfaced in generic queries despite both being long-established at
KBMQ. What worked better: querying each street address on the field
(2302 / 3202 / 3242 S. Water St) and pulling airport-specific directories.
OpenStreetMap was checked via the Overpass API and turned out to be *stale*
for this field (it lists a homebuilder at 3202 S. Water St, C3 Air's address),
so it is not a reliable source here. Treat this list as thorough but not
provably exhaustive; the airport office is the only authoritative tenant roll.

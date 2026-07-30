#!/usr/bin/env node
// Scrape https://evbreakers.com/donor-cars into ../cars.json
//
// The donor-cars listing paginates via an AJAX POST to the same URL with a
// `page` form field (see scripts.min.js `fetch_donor`). Each response is a
// full HTML page containing ~30 car cards. We walk pages until a page yields
// no new cars, parse every card, normalise the fields, and write cars.json.
//
// Usage: node scrape.js [--out ../cars.json]

const fs = require("fs");
const path = require("path");

const BASE = "https://evbreakers.com/donor-cars";
const OUT =
  process.argv.includes("--out")
    ? process.argv[process.argv.indexOf("--out") + 1]
    : path.join(__dirname, "..", "cars.json");

const sleep = (ms) => new Promise((r) => setTimeout(r, ms));

async function fetchPage(page) {
  const res = await fetch(BASE, {
    method: "POST",
    headers: {
      "Content-Type": "application/x-www-form-urlencoded",
      "X-Requested-With": "XMLHttpRequest",
    },
    body: `page=${page}`,
  });
  if (!res.ok) throw new Error(`page ${page}: HTTP ${res.status}`);
  return res.text();
}

// --- parsing ---------------------------------------------------------------

function parseCards(html) {
  const out = [];
  const cardRe = /<div class="shadow_1 card">([\s\S]*?)View Parts<\/a>/g;
  let m;
  while ((m = cardRe.exec(html))) {
    const card = m[1];
    const title = card.match(/<a href="\.\/donor-parts\?id=(\d+)">([^<]+)<\/a>/);
    if (!title) continue;
    const fields = {};
    const fieldRe = /<b>([^:<]+):\s*<\/b>([^<]*)/g;
    let fm;
    while ((fm = fieldRe.exec(card))) {
      fields[fm[1].trim()] = fm[2].trim().replace(/\s+/g, " ");
    }
    out.push({
      id: Number(title[1]),
      name: title[2].trim().replace(/\s+/g, " "),
      fields,
    });
  }
  return out;
}

// --- normalisation ---------------------------------------------------------

// Listing titles are "YYYY MAKE MODEL...". Fix the handful of aliases and
// two-word makes the site uses inconsistently.
const MAKE_ALIAS = {
  "ŠKODA": "SKODA",
  VW: "VOLKSWAGEN",
  "MERCEDES-BENZ": "MERCEDES",
  GREAT: "GREAT WALL",
  LAND: "LAND ROVER",
};

function splitName(name) {
  let year = null;
  let rest = name;
  const ym = rest.match(/^(\d{4})\s+(.*)$/);
  if (ym) {
    year = Number(ym[1]);
    rest = ym[2];
  }
  const words = rest.split(/\s+/);
  let make = (words.shift() || "").toUpperCase();
  // one listing is titled just "2022 CORSA" — that's a Vauxhall Corsa
  if (make === "CORSA") {
    words.unshift("CORSA");
    make = "VAUXHALL";
  }
  if (MAKE_ALIAS[make]) {
    const alias = MAKE_ALIAS[make];
    // two-word makes consume the next word ("GREAT WALL", "LAND ROVER")
    if (alias.includes(" ") && words.length) words.shift();
    make = alias;
  }
  return { year, make, model: words.join(" ") };
}

// Battery capacity only appears where the site put a kWh figure in the
// engine string or the title (e.g. "EM57 62KWH", "100 KWH (ZKX)").
function extractKwh(...texts) {
  for (const t of texts) {
    const m = (t || "").match(/([\d.]+)\s*KWH/i);
    if (m) return Number(m[1]);
  }
  return null;
}

function normalise(raw) {
  const { year, make, model } = splitName(raw.name);
  const engine = raw.fields["Engine"] || "";
  return {
    id: raw.id,
    name: raw.name,
    year,
    make,
    model,
    engine,
    kwh: extractKwh(engine, raw.name, raw.fields["Variant"]),
    variant: raw.fields["Variant"] || "",
    color: raw.fields["Body Color"] || "",
    url: `https://evbreakers.com/donor-parts?id=${raw.id}`,
    img: `https://evbreakers.com/image/eladene/evbreakers/donor_cars/500/${raw.id}`,
  };
}

// --- main ------------------------------------------------------------------

(async () => {
  const cars = new Map();
  let page = 1;
  for (;;) {
    const html = await fetchPage(page);
    const cards = parseCards(html);
    const before = cars.size;
    for (const c of cards) cars.set(c.id, c);
    console.log(`page ${page}: ${cards.length} cards, ${cars.size} total`);
    // stop when a page adds nothing new (past the last page the site
    // just returns the last page again) or is empty
    if (cards.length === 0 || cars.size === before) break;
    page++;
    await sleep(500);
  }

  const list = [...cars.values()].sort((a, b) => b.id - a.id).map(normalise);
  const data = {
    source: BASE,
    scraped: new Date().toISOString().slice(0, 10),
    count: list.length,
    cars: list,
  };
  fs.writeFileSync(OUT, JSON.stringify(data, null, 1));
  console.log(`wrote ${list.length} cars -> ${OUT}`);
})();

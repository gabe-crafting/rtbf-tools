#!/usr/bin/env node
// Inject ../cars.json into ../index.html so the page is standalone.
//
// index.html holds the dataset in <script id="cars-data" type="application/json">.
// This script replaces that block's contents with the current cars.json.
//
// Usage: node build_page.js

const fs = require("fs");
const path = require("path");

const root = path.join(__dirname, "..");
const dataPath = path.join(root, "cars.json");
const pagePath = path.join(root, "index.html");

const data = JSON.parse(fs.readFileSync(dataPath, "utf8"));
// </script> inside a JSON string would end the tag early; escape defensively.
const json = JSON.stringify(data).replace(/<\//g, "<\\/");

const page = fs.readFileSync(pagePath, "utf8");
const re = /(<script id="cars-data" type="application\/json">)[\s\S]*?(<\/script>)/;
if (!re.test(page)) {
  console.error("cars-data script block not found in index.html");
  process.exit(1);
}
fs.writeFileSync(pagePath, page.replace(re, `$1\n${json}\n$2`));
console.log(`embedded ${data.cars.length} cars (scraped ${data.scraped}) into index.html`);

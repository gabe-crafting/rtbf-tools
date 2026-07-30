#!/usr/bin/env node
// Inject ../followers.json into ../index.html so the page is standalone.
//
// index.html holds the dataset in <script id="followers-data" type="application/json">.
// This script replaces that block's contents with the current followers.json.
//
// Usage: node build_page.js

const fs = require("fs");
const path = require("path");

const root = path.join(__dirname, "..");
const data = JSON.parse(fs.readFileSync(path.join(root, "followers.json"), "utf8"));
// </script> inside a JSON string would end the tag early; escape defensively.
const json = JSON.stringify(data).replace(/<\//g, "<\\/");

const pagePath = path.join(root, "index.html");
const page = fs.readFileSync(pagePath, "utf8");
const re = /(<script id="followers-data" type="application\/json">)[\s\S]*?(<\/script>)/;
if (!re.test(page)) {
  console.error("followers-data script block not found in index.html");
  process.exit(1);
}
// Replacer must be a function: the JSON itself can contain `$1`, `$2`, `$&`...
// which String.replace would otherwise expand as capture-group references.
fs.writeFileSync(pagePath,
  page.replace(re, (m, open, close) => `${open}\n${json}\n${close}`));
console.log(`embedded ${data.followers.length} followers (scraped ${data.scraped}) into index.html`);

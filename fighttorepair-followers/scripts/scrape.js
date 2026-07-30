#!/usr/bin/env node
// Scrape the public follower list of a Substack profile plus each follower's
// most recent public like/reply, into ../followers.json.
//
// Public, unauthenticated endpoints (all on substack.com/api/v1):
//   profile    /user/<handle>/public_profile
//   followers  /user/<id>/subscriber-lists?lists=followers
//   activity   /reader/feed/profile/<id>?types[]=like&types[]=replies
//
// The followers endpoint only returns the profiles Substack exposes publicly
// (a few hundred), not the full follower count shown on the profile page.
// The activity feed is newest-first, so its first item is the user's latest
// like or reply.
//
// Usage: node scrape.js [--handle fighttorepair] [--out ../followers.json]

const fs = require("fs");
const path = require("path");
const { execFileSync } = require("child_process");

const arg = (name, dflt) => {
  const i = process.argv.indexOf(name);
  return i > -1 ? process.argv[i + 1] : dflt;
};
const HANDLE = arg("--handle", "fighttorepair");
const OUT = arg("--out", path.join(__dirname, "..", "followers.json"));

const API = "https://substack.com/api/v1";
// Cloudflare fronts some endpoints; a browser-ish UA + Referer gets through.
const HEADERS = {
  "User-Agent":
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36",
  Accept: "application/json",
  "Accept-Language": "en-US,en;q=0.9",
  Referer: `https://substack.com/@${HANDLE}/followers`,
};

const sleep = (ms) => new Promise((r) => setTimeout(r, ms));

// Cloudflare challenges Node's fetch (TLS fingerprint) on some of these
// endpoints but lets curl through, so all requests go via the curl binary
// (bundled with Windows 10+, macOS, and virtually every Linux).
async function getJson(url, retries = 4) {
  const args = [
    "-s", "--max-time", "45",
    ...Object.entries(HEADERS).flatMap(([k, v]) => ["-H", `${k}: ${v}`]),
    url,
  ];
  let delay = 1500;
  for (let i = 0; i < retries; i++) {
    try {
      const body = execFileSync("curl", args, { encoding: "utf8", maxBuffer: 64e6 });
      return JSON.parse(body); // HTML (403/404/challenge page) lands in catch
    } catch (e) {
      if (i === retries - 1) console.error(`  ! ${e.message.slice(0, 120)} ${url}`);
    }
    await sleep(delay);
    delay *= 2;
  }
  return null;
}

// The feed mixes item shapes; classify into like/reply and describe the target.
function summariseActivity(item) {
  const ctx = (item.context && item.context.type) || "";
  const kind = ctx.endsWith("_like") ? "like" : "reply";
  let what = "";
  if (item.post) {
    what = item.post.title || "";
  } else if (item.comment) {
    what = (item.comment.body || "").replace(/\s+/g, " ").slice(0, 90);
  }
  return {
    date: ((item.context && item.context.timestamp) || "").slice(0, 10),
    kind,
    ctx, // post_like / note_like / comment / note_reply
    what,
  };
}

(async () => {
  console.error(`profile @${HANDLE} ...`);
  const profile = await getJson(`${API}/user/${HANDLE}/public_profile`);
  if (!profile) throw new Error("could not fetch public_profile");
  console.error(`  id ${profile.id}, ${profile.followerCount} followers total`);

  const lists = await getJson(
    `${API}/user/${profile.id}/subscriber-lists?lists=followers`);
  const groups =
    ((lists && lists.subscriberLists) || []).find((l) => l.id === "followers");
  const users = (groups ? groups.groups : []).flatMap((g) => g.users || []);
  console.error(`  ${users.length} followers publicly listed`);
  if (!users.length) throw new Error("no followers returned");

  const followers = [];
  for (const [i, u] of users.entries()) {
    const feed = await getJson(
      `${API}/reader/feed/profile/${u.id}?types%5B%5D=like&types%5B%5D=replies`);
    const item = feed && feed.items && feed.items[0];
    const pub = u.primary_publication;
    followers.push({
      id: u.id,
      name: u.name || u.handle,
      handle: u.handle,
      photo: u.photo_url || null,
      bio: (u.bio || "").trim(),
      pub: pub ? pub.name : null,
      pub_url: pub
        ? pub.custom_domain
          ? `https://${pub.custom_domain}`
          : `https://${pub.subdomain}.substack.com`
        : null,
      tier: u.bestseller_tier || 0,
      last: item ? summariseActivity(item) : null,
    });
    console.error(
      `  [${i + 1}/${users.length}] @${u.handle} -> ` +
      (item ? `${followers[i].last.kind} ${followers[i].last.date}` : "no public activity"));
    await sleep(300);
  }

  const data = {
    handle: HANDLE,
    profile_name: profile.name,
    profile_user_id: profile.id,
    follower_count_total: profile.followerCount,
    follower_count_public: followers.length,
    scraped: new Date().toISOString().slice(0, 10),
    followers,
  };
  fs.writeFileSync(OUT, JSON.stringify(data, null, 1));
  console.error(`wrote ${followers.length} followers -> ${OUT}`);
})();

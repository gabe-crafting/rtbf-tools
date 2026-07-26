# -*- coding: utf-8 -*-
"""
Render a scraped dataset into a standalone, searchable HTML page.

The data is embedded in the file, so the result works offline, over file://,
and on any static host (GitHub Pages included) with no server or fetch calls.
Any number of tags is supported; each gets its own colour and filter chip.

Examples
--------
  python build_page.py --data ../substack_accounts.json --out ../index.html
  python build_page.py -d data.json -o site/index.html --title "Health Substacks"
"""

import argparse
import io
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from substack_lib import eprint, load_json, slugify

# Distinguishable in both light and dark themes.
PALETTE = ["#ff7a45", "#4f9dff", "#3ecf8e", "#c084fc", "#f5c542",
           "#ff5c8a", "#22d3ee", "#a3e635", "#fb923c", "#818cf8"]

TEMPLATE = r"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>__TITLE__</title>
<style>
  :root{
    --bg:#0f1115; --card:#181b22; --card2:#1f232c; --line:#2a2f3a;
    --text:#e8eaed; --muted:#9aa3af; --accent:#ff7a45; --accent2:#4f9dff;
  }
  @media (prefers-color-scheme: light){
    :root{--bg:#f5f6f8;--card:#fff;--card2:#f0f2f5;--line:#e2e5ea;--text:#1a1d23;--muted:#606874;}
  }
  *{box-sizing:border-box}
  body{margin:0;background:var(--bg);color:var(--text);font:15px/1.5 -apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,Helvetica,Arial,sans-serif}
  .wrap{max-width:1080px;margin:0 auto;padding:28px 20px 60px}
  h1{font-size:26px;margin:0 0 4px}
  .sub{color:var(--muted);margin:0 0 22px;font-size:14px}
  .controls{display:grid;grid-template-columns:1fr auto auto auto;gap:12px;align-items:end;margin-bottom:8px}
  @media(max-width:760px){.controls{grid-template-columns:1fr 1fr}}
  .fld{display:flex;flex-direction:column;gap:5px}
  .fld label{font-size:11px;text-transform:uppercase;letter-spacing:.5px;color:var(--muted)}
  input[type=search],select{background:var(--card);border:1px solid var(--line);color:var(--text);
    border-radius:9px;padding:10px 12px;font-size:14px;outline:none;width:100%}
  input[type=search]:focus,select:focus{border-color:var(--accent)}
  .rangewrap{display:flex;flex-direction:column;gap:5px;min-width:180px}
  .rangewrap .val{font-size:12px;color:var(--muted)}
  input[type=range]{accent-color:var(--accent);width:100%}
  .meta{display:flex;justify-content:space-between;align-items:center;margin:14px 0 10px;color:var(--muted);font-size:13px;flex-wrap:wrap;gap:8px}
  .chips{display:flex;gap:8px;flex-wrap:wrap}
  .chip{border:1px solid var(--line);background:var(--card);border-radius:20px;padding:5px 12px;cursor:pointer;font-size:13px;color:var(--muted)}
  .chip.on{color:#fff;border-color:transparent}
  .chip.on[data-k="__all__"]{background:#6b7280}
__CHIP_CSS__
  table{width:100%;border-collapse:collapse;font-size:14px}
  thead th{text-align:left;color:var(--muted);font-weight:600;font-size:12px;text-transform:uppercase;
    letter-spacing:.4px;padding:8px 10px;border-bottom:1px solid var(--line);cursor:pointer;white-space:nowrap}
  thead th .ar{opacity:.4;font-size:10px}
  tbody td{padding:12px 10px;border-bottom:1px solid var(--line);vertical-align:top}
  tr.main.expandable{cursor:pointer}
  tr.main.expandable:hover{background:var(--card2)}
  tr.main.open{background:var(--card2)}
  .caret{display:inline-block;width:14px;color:var(--muted);transition:transform .15s;font-size:11px}
  tr.main.open .caret{transform:rotate(90deg);color:var(--accent2)}
  .nm{font-weight:600}
  .nm a{color:inherit;text-decoration:none}
  .nm a:hover{text-decoration:underline}
  .pub{color:var(--muted);font-size:12.5px;margin-top:2px;padding-left:14px}
  .pub a{color:var(--accent2);text-decoration:none}
  .num{font-variant-numeric:tabular-nums;white-space:nowrap}
  .big{font-weight:600}
  .kw{display:inline-block;font-size:11px;font-weight:600;padding:2px 8px;border-radius:6px;color:#fff;margin:0 4px 3px 0}
  .tier{font-size:11px;color:var(--muted)}
  .empty{padding:40px;text-align:center;color:var(--muted)}
  .foot{margin-top:24px;color:var(--muted);font-size:12px}
  tr.detail>td{padding:0;border-bottom:1px solid var(--line);background:var(--bg)}
  .acc{display:grid;grid-template-columns:1fr 1fr;gap:0}
  @media(max-width:720px){.acc{grid-template-columns:1fr}}
  .panel{padding:14px 16px}
  .panel+.panel{border-left:1px solid var(--line)}
  @media(max-width:720px){.panel+.panel{border-left:none;border-top:1px solid var(--line)}}
  .panel h4{margin:0 0 10px;font-size:12px;text-transform:uppercase;letter-spacing:.5px;color:var(--muted)}
  .post{padding:7px 0;border-bottom:1px dashed var(--line)}
  .post:last-child{border-bottom:none}
  .post a{color:var(--text);text-decoration:none;font-weight:500;font-size:13.5px;line-height:1.35;display:block}
  .post a:hover{color:var(--accent2)}
  .post .pmeta{font-size:11.5px;color:var(--muted);margin-top:3px;font-variant-numeric:tabular-nums}
  .post .pmeta .g{margin-right:9px}
  .lock{opacity:.55;font-size:10px}
  .rank{display:inline-block;min-width:16px;color:var(--muted);font-weight:700;font-size:11px}
  /* who may comment on a post -- independent of who may read it */
  .cacc{display:inline-block;font-size:10px;font-weight:700;padding:1px 6px;border-radius:5px;
    text-transform:uppercase;letter-spacing:.3px;white-space:nowrap}
  .cacc.everyone{background:rgba(62,207,142,.15);color:#3ecf8e;border:1px solid rgba(62,207,142,.35)}
  .cacc.subscribers{background:rgba(79,157,255,.15);color:#4f9dff;border:1px solid rgba(79,157,255,.35)}
  .cacc.paid{background:rgba(245,197,66,.15);color:#f5c542;border:1px solid rgba(245,197,66,.35)}
  .cacc.none,.cacc.unknown{background:rgba(154,163,175,.13);color:var(--muted);border:1px solid var(--line)}
  @media (prefers-color-scheme: light){
    .cacc.everyone{color:#0f7a4d}
    .cacc.subscribers{color:#1b5fbe}
    .cacc.paid{color:#8a6300}
  }
  .legend{display:inline-block;margin-right:10px}
</style>
</head>
<body>
<div class="wrap">
  <h1>__HEADING__</h1>
  <p class="sub">__SUBTITLE__</p>

  <div class="controls">
    <div class="fld">
      <label>Search by name / publication / bio</label>
      <input id="q" type="search" placeholder="Type a name..." autocomplete="off">
    </div>
    <div class="fld">
      <label>Sort by</label>
      <select id="sort">
        <option value="followers">Followers</option>
        <option value="subscribers_number">Subscribers</option>
        <option value="started">Start date</option>
        <option value="name">Name</option>
      </select>
    </div>
    <div class="fld">
      <label>Order</label>
      <select id="order"><option value="desc">High &rarr; Low</option><option value="asc">Low &rarr; High</option></select>
    </div>
    <div class="rangewrap fld">
      <label>Min followers</label>
      <input id="minf" type="range" min="0" max="__MAXF__" step="__STEP__" value="0">
      <span class="val" id="minfval">0+</span>
    </div>
  </div>

  <div class="meta">
    <div class="chips" id="chips">__CHIPS__</div>
    <div id="count"></div>
  </div>

  <table>
    <thead><tr>
      <th data-s="name">Account <span class="ar"></span></th>
      <th data-s="followers">Followers <span class="ar"></span></th>
      <th data-s="subscribers_number">Subscribers <span class="ar"></span></th>
      <th data-s="started">Started <span class="ar"></span></th>
      <th data-s="keywords">Keywords <span class="ar"></span></th>
    </tr></thead>
    <tbody id="rows"></tbody>
  </table>
  <div class="empty" id="empty" style="display:none">No accounts match your filters.</div>

  <p class="foot">__FOOTER__</p>
</div>

<script>
const DATA = __DATA__;
const KWMAP = __KWMAP__;
const $ = s => document.querySelector(s);
let kw = "__all__";

function fmt(n){ if(!n) return "0"; if(n>=1000) return (n/1000).toFixed(n>=100000?0:1).replace(/\.0$/,'')+"K"; return ""+n; }
function dfmt(s){ if(!s) return "—"; const d=new Date(s); return isNaN(d)?"—":d.toLocaleDateString('en-US',{year:'numeric',month:'short',day:'numeric'}); }
function esc(s){ return (s||"").replace(/[&<>"]/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c])); }
function kwSlug(k){ return (KWMAP[k]||{}).slug || "tag"; }

// Who may COMMENT. Separate from who may READ (the padlock) -- a free-to-read
// post can still be paid-only for commenting, and vice versa.
const CACC = {
  everyone:    {label:"free",  title:"Comments open to everyone"},
  subscribers: {label:"subs",  title:"Only subscribers (free or paid) can comment"},
  paid:        {label:"paid",  title:"Only paid subscribers can comment"},
  none:        {label:"off",   title:"Comments are closed"},
  unknown:     {label:"n/a",   title:"Comment access not reported"}
};
function caccBadge(p){
  const key = p.comment_access || "unknown";
  const meta = CACC[key] || {label:key, title:"Comment access: "+key};
  const cls = key.replace(/[^a-z0-9]+/gi,'-').toLowerCase();
  return `<span class="cacc ${cls}" title="${esc(meta.title)}">&#128172; ${esc(meta.label)}</span>`;
}

function postRow(p, rank){
  const lock = (p.audience && p.audience!=="everyone") ? ' <span class="lock" title="paid subscribers only can read">&#128274;</span>' : '';
  const r = rank!=null ? `<span class="rank">${rank}.</span> ` : '';
  return `<div class="post">
    <a href="${p.url}" target="_blank" rel="noopener">${r}${esc(p.title)}${lock}</a>
    <div class="pmeta"><span class="g">${dfmt(p.date)}</span><span class="g">&#10084; ${fmt(p.reactions)}</span><span class="g">&#128172; ${fmt(p.comments)}</span><span class="g">&#9851; ${fmt(p.restacks)}</span>${caccBadge(p)}</div>
  </div>`;
}

function accordion(a){
  const recent = a.recent_posts||[], top = a.top_posts||[];
  return `<tr class="detail" hidden><td colspan="5"><div class="acc">
    <div class="panel"><h4>&#128336; Most recent posts</h4>${recent.map(p=>postRow(p,null)).join("")}</div>
    <div class="panel"><h4>&#128293; Most engaged posts</h4>${top.map((p,i)=>postRow(p,i+1)).join("")}</div>
  </div></td></tr>`;
}

function render(){
  const q = $("#q").value.trim().toLowerCase();
  const sort = $("#sort").value, order = $("#order").value, minf = +$("#minf").value;
  $("#minfval").textContent = fmt(minf)+"+";
  let rows = DATA.filter(a=>{
    if(kw!=="__all__" && !a.keywords.includes(kw)) return false;
    if(a.followers < minf) return false;
    if(q){
      const hay = (a.name+" "+(a.publication||"")+" "+(a.bio||"")+" "+a.handle).toLowerCase();
      if(!hay.includes(q)) return false;
    }
    return true;
  });
  rows.sort((x,y)=>{
    let vx=x[sort], vy=y[sort];
    if(sort==="name"){ vx=(vx||"").toLowerCase(); vy=(vy||"").toLowerCase();
      return order==="asc"?(vx<vy?-1:vx>vy?1:0):(vx>vy?-1:vx<vy?1:0); }
    if(sort==="started"){ vx=new Date(vx||0).getTime(); vy=new Date(vy||0).getTime(); }
    if(sort==="keywords"){ vx=x.keywords.length; vy=y.keywords.length; }
    return order==="asc"? vx-vy : vy-vx;
  });
  $("#count").textContent = rows.length+" of "+DATA.length+" accounts";
  $("#rows").innerHTML = rows.map(a=>{
    const hasPosts = (a.recent_posts&&a.recent_posts.length) || (a.top_posts&&a.top_posts.length);
    const caret = `<span class="caret">${hasPosts?"▶":""}</span> `;
    const pool = hasPosts ? ` &middot; <span class="tier">${a.post_pool} posts</span>` : '';
    const tier = a.bestseller_tier ? ` &middot; <span class="tier">bestseller ${fmt(a.bestseller_tier)}</span>` : '';
    const main = `<tr class="main ${hasPosts?'expandable':''}">
        <td>
          <div class="nm">${caret}<a href="${a.profile_url}" target="_blank" rel="noopener">${esc(a.name)}</a></div>
          <div class="pub">${a.publication?`<a href="${a.publication_url}" target="_blank" rel="noopener">${esc(a.publication)}</a>`:'@'+esc(a.handle)}${tier}${pool}</div>
        </td>
        <td class="num big">${fmt(a.followers)}</td>
        <td class="num">${a.subscribers_label?esc(a.subscribers_label.replace(' subscribers','')):fmt(a.subscribers_number)}</td>
        <td class="num">${dfmt(a.started)}</td>
        <td>${a.keywords.map(k=>`<span class="kw ${kwSlug(k)}">${esc(k)}</span>`).join('')}</td>
      </tr>`;
    return main + (hasPosts ? accordion(a) : "");
  }).join("");
  $("#empty").style.display = rows.length? "none":"block";
  document.querySelectorAll("thead th").forEach(th=>{
    th.querySelector(".ar").textContent = th.dataset.s===sort ? (order==="asc"?"▲":"▼") : "";
  });
}

$("#q").addEventListener("input", render);
$("#sort").addEventListener("change", render);
$("#order").addEventListener("change", render);
$("#minf").addEventListener("input", render);
$("#chips").addEventListener("click", e=>{
  const c = e.target.closest(".chip"); if(!c) return;
  kw = c.dataset.k;
  document.querySelectorAll(".chip").forEach(x=>x.classList.toggle("on", x.dataset.k===kw));
  render();
});
$("#rows").addEventListener("click", e=>{
  if(e.target.closest("a")) return;                    // let links through
  const tr = e.target.closest("tr.main.expandable"); if(!tr) return;
  const det = tr.nextElementSibling;
  if(det && det.classList.contains("detail")){
    if(det.hasAttribute("hidden")){ det.removeAttribute("hidden"); tr.classList.add("open"); }
    else { det.setAttribute("hidden",""); tr.classList.remove("open"); }
  }
});
document.querySelectorAll("thead th").forEach(th=>th.addEventListener("click",()=>{
  const s = th.dataset.s;
  if($("#sort").value===s){ $("#order").value = $("#order").value==="asc"?"desc":"asc"; }
  else { $("#sort").value=s; $("#order").value = s==="name"?"asc":"desc"; }
  render();
}));
render();
</script>
</body>
</html>"""


def parse_args():
    ap = argparse.ArgumentParser(description="Build a searchable HTML page from scraped data.")
    ap.add_argument("-d", "--data", default="substack_accounts.json", help="input JSON from scrape.py")
    ap.add_argument("-o", "--out", default="index.html", help="output HTML path")
    ap.add_argument("--title", default=None, help="page title (default: derived from tags)")
    ap.add_argument("--heading", default=None, help="on-page H1 (default: same as --title)")
    return ap.parse_args()


def main():
    args = parse_args()

    data = load_json(args.data)
    if not data or not data.get("accounts"):
        eprint("No accounts found in %s -- run scrape.py first." % args.data)
        return 1

    accounts = data["accounts"]
    tags = data.get("queries") or sorted({t for a in accounts for t in a["keywords"]})

    # tag -> {slug, color}
    kwmap, chip_css, chips = {}, [], ['<span class="chip on" data-k="__all__">All</span>']
    for i, tag in enumerate(tags):
        slug, color = slugify(tag), PALETTE[i % len(PALETTE)]
        kwmap[tag] = {"slug": slug, "color": color}
        chip_css.append("  .kw.%s{background:%s}" % (slug, color))
        chip_css.append('  .chip.on[data-k="%s"]{background:%s}' % (tag.replace('"', '\\"'), color))
        chips.append('<span class="chip" data-k="%s">%s</span>'
                     % (tag.replace('"', "&quot;"), tag))

    pretty = " & ".join(t.title() for t in tags) if tags else "Substack"
    title = args.title or ("Substack Accounts - " + pretty)
    heading = args.heading or args.title or "Substack Accounts"

    coloured = ", ".join('<b style="color:%s">%s</b>' % (kwmap[t]["color"], t) for t in tags)
    with_posts = sum(1 for a in accounts if a.get("recent_posts"))
    subtitle = ("Accounts surfaced by searching Substack for %s. "
                "Data pulled %s &middot; %d accounts. "
                "Click any row to expand recent &amp; most-engaged posts."
                % (coloured, data.get("generated", "n/a"), len(accounts)))

    pools = [a.get("post_pool", 0) for a in accounts if a.get("post_pool")]
    legend = ('<b>Who can comment:</b> '
              '<span class="legend"><span class="cacc everyone">&#128172; free</span> anyone</span>'
              '<span class="legend"><span class="cacc subscribers">&#128172; subs</span> subscribers (free or paid)</span>'
              '<span class="legend"><span class="cacc paid">&#128172; paid</span> paid subscribers only</span>'
              '<span class="legend"><span class="cacc none">&#128172; off</span> closed</span>'
              '<br>This is separate from who can <em>read</em> a post &mdash; '
              '&#128274; marks a paid-only post, and a free post can still be paid-only for commenting.<br>')
    footer = (legend +
              "Followers &amp; subscribers come from each account's public Substack profile. "
              "&quot;Started&quot; is the date the account's publication was created "
              "(its first-post period). &quot;Keywords&quot; shows which search term surfaced "
              "the account. Posts are drawn from up to the %d most recent per account "
              "(%d of %d accounts have post data); &quot;most engaged&quot; = reactions + "
              "comments + restacks <em>within that window</em>, not all-time."
              % (max(pools) if pools else 0, with_posts, len(accounts)))

    maxf = max((a.get("followers", 0) for a in accounts), default=1000) or 1000
    html = (TEMPLATE
            .replace("__CHIP_CSS__", "\n".join(chip_css))
            .replace("__CHIPS__", "".join(chips))
            .replace("__DATA__", json.dumps(accounts, ensure_ascii=False))
            .replace("__KWMAP__", json.dumps(kwmap, ensure_ascii=False))
            .replace("__TITLE__", title)
            .replace("__HEADING__", heading)
            .replace("__SUBTITLE__", subtitle)
            .replace("__FOOTER__", footer)
            .replace("__MAXF__", str(int(maxf)))
            .replace("__STEP__", str(max(100, int(maxf / 500) * 100))))

    out_dir = os.path.dirname(os.path.abspath(args.out))
    if out_dir and not os.path.isdir(out_dir):
        os.makedirs(out_dir)
    with io.open(args.out, "w", encoding="utf-8") as f:
        f.write(html)

    eprint("Wrote %s (%.1f KB) -- %d accounts, %d tag(s): %s"
           % (args.out, len(html) / 1024.0, len(accounts), len(tags), ", ".join(tags)))
    return 0


if __name__ == "__main__":
    sys.exit(main())

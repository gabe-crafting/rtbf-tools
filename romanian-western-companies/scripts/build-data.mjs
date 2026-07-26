import { readFileSync, writeFileSync, readdirSync } from "fs";
import { join, dirname } from "path";
import { fileURLToPath } from "url";

const root = join(dirname(fileURLToPath(import.meta.url)), "..");
const companiesDir = join(root, "companies");
const parentsDir = join(root, "parents");
const readme = readFileSync(join(root, "README.md"), "utf8");

const westernLinkBySlug = {};
for (const line of readme.split("\n")) {
  const match = line.match(
    /\|\s*\d+\s*\|\s*([^|]+)\|\s*(\d+)\s*\|[^|]*\|\s*[^|]*\|\s*([^|]+)\|\s*\[profile\]\(companies\/([^)]+)\)/
  );
  if (match) {
    westernLinkBySlug[match[4].replace(".md", "")] = {
      name: match[1].trim(),
      cui: match[2].trim(),
      westernLink: match[3].trim(),
    };
  }
}

const NATIONALITY_ALIASES = {
  german: ["german", "germany", "deutsch"],
  british: ["british", "uk", "english", "england"],
  scottish: ["scottish", "scotland"],
  french: ["french", "france"],
  austrian: ["austrian", "austria"],
  italian: ["italian", "italy", "tyrolean", "tyrol"],
  czech: ["czech", "czechia"],
  finnish: ["finnish", "finland"],
  danish: ["danish", "denmark"],
};

function extractNationalities(...texts) {
  const haystack = texts.join(" ").toLowerCase();
  const found = new Set();
  for (const [canonical, aliases] of Object.entries(NATIONALITY_ALIASES)) {
    if (aliases.some((alias) => haystack.includes(alias))) {
      found.add(canonical);
    }
  }
  return [...found].sort();
}

function parseEmployees(raw) {
  if (!raw) return { employees: null, employeesLabel: "" };

  const numbers = [...raw.matchAll(/\d+/g)].map((m) => Number(m[0]));
  const filedMatch = raw.match(/(\d+)\s*filed/i);
  const employees = filedMatch ? Number(filedMatch[1]) : numbers[0] ?? null;

  return { employees, employeesLabel: raw.trim() };
}

function parseProfile(md, slug) {
  const title = md.match(/^# (.+)$/m)?.[1] ?? slug;
  const trading = md.match(/\*\*Trading[^:]*:\*\*\s*(.+)/)?.[1] ?? "";
  const background =
    md.match(/\*\*Reported background[^:]*:\*\*\s*(.+)/)?.[1] ?? "";
  const label = md.match(/\*\*Label:\*\*\s*(.+)/)?.[1] ?? "";
  const employeesRaw = md.match(/\*\*Employees:\*\*\s*(.+)/)?.[1] ?? "";
  const { employees, employeesLabel } = parseEmployees(employeesRaw);
  const meta = westernLinkBySlug[slug] ?? {};

  const nationalities = extractNationalities(
    meta.westernLink ?? "",
    background,
    md
  );

  return {
    slug,
    name: title,
    tradingName: trading,
    cui: meta.cui ?? md.match(/\*\*CUI:\*\*\s*(\d+)/)?.[1] ?? "",
    westernLink: meta.westernLink ?? "",
    nationalities,
    label,
    employees,
    employeesLabel,
    markdown: md,
  };
}

const files = readdirSync(companiesDir).filter((f) => f.endsWith(".md"));
const companies = files
  .map((file) => {
    const slug = file.replace(".md", "");
    const md = readFileSync(join(companiesDir, file), "utf8");
    return parseProfile(md, slug);
  })
  .sort((a, b) => a.name.localeCompare(b.name));

function parseParent(md, slug) {
  const title = md.match(/^# (.+)$/m)?.[1] ?? slug;
  return { slug, name: title, markdown: md };
}

const parentFiles = readdirSync(parentsDir).filter((f) => f.endsWith(".md"));
const parents = parentFiles
  .map((file) => {
    const slug = file.replace(".md", "");
    const md = readFileSync(join(parentsDir, file), "utf8");
    return parseParent(md, slug);
  })
  .sort((a, b) => a.name.localeCompare(b.name));

const payload = {
  generated: new Date().toISOString().slice(0, 10),
  companies,
  parents,
};

writeFileSync(join(root, "data", "companies.json"), JSON.stringify(payload, null, 2));

writeFileSync(
  join(root, "js", "companies-data.js"),
  `window.COMPANIES_DATA = ${JSON.stringify(payload)};\n`
);

console.log(
  `Wrote ${companies.length} companies and ${parents.length} parents to data/companies.json and js/companies-data.js`
);

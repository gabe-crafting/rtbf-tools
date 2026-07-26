#!/usr/bin/env bash
# Commit the generated site and publish it via GitHub Pages.
#
#   ./deploy.sh                                   # commit+push, enable Pages if needed
#   ./deploy.sh -m "refresh data"                 # custom commit message
#   ./deploy.sh -b main -f "index.html data.json" # explicit branch / files
#   ./deploy.sh --no-pages                        # just commit and push
#
# The GitHub token is read from git's credential helper (never printed, never
# stored). It needs the `repo` scope. Pages on a free account requires the
# repository to be PUBLIC -- the script warns before enabling it on a private one.

set -euo pipefail

BRANCH=""
MESSAGE="Update Substack account directory"
FILES="index.html substack_accounts.json README.md"
ENABLE_PAGES=1

while [[ $# -gt 0 ]]; do
  case "$1" in
    -b|--branch)   BRANCH="$2"; shift 2 ;;
    -m|--message)  MESSAGE="$2"; shift 2 ;;
    -f|--files)    FILES="$2";   shift 2 ;;
    --no-pages)    ENABLE_PAGES=0; shift ;;
    -h|--help)     sed -n '2,14p' "$0"; exit 0 ;;
    *) echo "Unknown option: $1" >&2; exit 1 ;;
  esac
done

cd "$(dirname "$0")/.."
command -v git >/dev/null || { echo "git not found" >&2; exit 1; }
git rev-parse --git-dir >/dev/null 2>&1 || { echo "Not a git repository." >&2; exit 1; }

REMOTE_URL=$(git remote get-url origin 2>/dev/null || true)
[[ -n "$REMOTE_URL" ]] || { echo "No 'origin' remote. Add one first." >&2; exit 1; }

# owner/repo from either https:// or git@ form
SLUG=$(printf '%s' "$REMOTE_URL" | sed -E 's#^git@github\.com:#https://github.com/#' \
        | sed -E 's#^https://github\.com/##; s#\.git$##')
[[ -n "$BRANCH" ]] || BRANCH=$(git rev-parse --abbrev-ref HEAD)

echo "Repository : $SLUG"
echo "Branch     : $BRANCH"
echo "Files      : $FILES"

# ----------------------------------------------------------- commit & push
git add -- $FILES 2>/dev/null || true
if git diff --cached --quiet; then
  echo "No staged changes; nothing to commit."
else
  git commit -q -m "$MESSAGE"
  echo "Committed: $(git log --oneline -1)"
fi

echo "Pushing to origin/$BRANCH ..."
git push origin "$BRANCH"

[[ "$ENABLE_PAGES" -eq 1 ]] || { echo "Done (Pages step skipped)."; exit 0; }

# ------------------------------------------------------------------- pages
TOKEN=$(printf 'protocol=https\nhost=github.com\n\n' | git credential fill 2>/dev/null \
        | sed -n 's/^password=//p')
if [[ -z "$TOKEN" ]]; then
  echo
  echo "No stored GitHub credential found, so Pages can't be configured here."
  echo "Enable it manually: https://github.com/$SLUG/settings/pages"
  exit 0
fi

api() { curl -sS -H "Authorization: token $TOKEN" -H "Accept: application/vnd.github+json" \
             -H "User-Agent: deploy-script" "$@"; }

VISIBILITY=$(api "https://api.github.com/repos/$SLUG" | sed -n 's/.*"visibility": *"\([^"]*\)".*/\1/p' | head -1)
echo "Visibility : ${VISIBILITY:-unknown}"

PAGES_CODE=$(api -o /dev/null -w '%{http_code}' "https://api.github.com/repos/$SLUG/pages")

if [[ "$PAGES_CODE" == "404" ]]; then
  if [[ "$VISIBILITY" == "private" ]]; then
    echo
    echo "WARNING: this repository is private. GitHub Pages on a free plan requires"
    echo "a public repository, and publishing makes the site world-readable."
    read -r -p "Enable Pages anyway? [y/N] " reply
    [[ "$reply" =~ ^[Yy]$ ]] || { echo "Aborted; changes are pushed but not published."; exit 0; }
  fi
  echo "Enabling GitHub Pages (branch: $BRANCH, path: /) ..."
  api -X POST "https://api.github.com/repos/$SLUG/pages" \
      -d "{\"source\":{\"branch\":\"$BRANCH\",\"path\":\"/\"}}" >/dev/null
else
  echo "GitHub Pages already enabled; the push triggers a rebuild."
fi

printf 'Waiting for build '
for _ in $(seq 1 30); do
  STATUS=$(api "https://api.github.com/repos/$SLUG/pages/builds/latest" \
           | sed -n 's/.*"status": *"\([^"]*\)".*/\1/p' | head -1)
  case "$STATUS" in
    built)   echo " done."; break ;;
    errored) echo " BUILD FAILED -- see https://github.com/$SLUG/settings/pages" >&2; exit 1 ;;
    *)       printf '.'; sleep 6 ;;
  esac
done

URL=$(api "https://api.github.com/repos/$SLUG/pages" | sed -n 's/.*"html_url": *"\([^"]*\)".*/\1/p' | head -1)
echo
echo "Live: ${URL:-https://github.com/$SLUG/settings/pages}"

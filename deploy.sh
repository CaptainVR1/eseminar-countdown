#!/usr/bin/env bash
# Ship the countdown widget.
#
# Primary home is our own box: https://app.tihe.ir/countdown/ — public, no SSO,
# and frameable (see the /countdown/ location in the nginx site). The widget has
# to be served over https because eseminar.tv is https and would block an http
# iframe as mixed content; that constraint, not GitHub, is the reason this was
# ever hosted externally.
#
# GitHub Pages is still updated as a mirror so embeds already published against
# the old URL keep working. Nothing new should point at it.
set -euo pipefail

SRC="/srv/Eseminar"
WEB="/var/www/app-tihe/countdown"

echo "→ $WEB"
mkdir -p "$WEB"
rsync -a "$SRC/countdown.html" "$SRC/logo.png" "$WEB/"
rsync -a --delete "$SRC/targets/" "$WEB/targets/"

# The VPS http site serves straight out of /srv/Eseminar, so it needs no copy.

if [ "${1:-}" = "--no-github" ]; then
  echo "→ skipping GitHub Pages mirror"
else
  echo "→ GitHub Pages mirror"
  "$SRC/sync-to-github.sh" || echo "!! GitHub mirror failed — the app.tihe.ir copy is live regardless"
fi

echo
echo "live: https://app.tihe.ir/countdown/countdown.html"
curl -s -o /dev/null -w "      HTTP %{http_code}\n" \
  "https://app.tihe.ir/countdown/countdown.html"

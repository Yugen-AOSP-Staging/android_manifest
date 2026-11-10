#!/usr/bin/env bash
#
# Regenerate default.xml from an upstream AOSP tag.
#
#   ./tools/gen-manifest.sh android-17.0.0_r1
#
# SPDX-License-Identifier: Apache-2.0
set -euo pipefail

TAG="${1:-android-17.0.0_r1}"
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
URL="https://android.googlesource.com/platform/manifest/+/refs/tags/${TAG}/default.xml?format=TEXT"

tmp="$(mktemp)"
trap 'rm -f "$tmp"' EXIT

echo "==> fetching AOSP manifest for $TAG"
curl -fsSL "$URL" | base64 -d > "$tmp"

python3 - "$tmp" "$ROOT/default.xml" <<'PY'
import sys

src, dst = sys.argv[1], sys.argv[2]
s = open(src).read()

# AOSP's manifest uses fetch="..", which is relative to android.googlesource.com.
# Our manifest is hosted on GitHub, so it must be absolute.
old = '''  <remote  name="aosp"
           fetch=".."
           review="https://android-review.googlesource.com/" />'''
new = '''  <remote  name="aosp"
           fetch="https://android.googlesource.com"
           review="https://android-review.googlesource.com/" />'''
if old not in s:
    sys.exit("aosp remote block not found; AOSP changed the manifest format")
s = s.replace(old, new, 1)

includes = '''
  <!-- ==== Project Yugen ==== -->
  <include name="snippets/remote.xml" />
  <include name="snippets/remove.xml" />
  <include name="snippets/external.xml" />
  <include name="snippets/custom.xml" />
  <include name="snippets/devices.xml" />
'''
s = s.replace("\n</manifest>", includes + "\n</manifest>")

open(dst, "w").write(s)
print(f"wrote {dst}: {s.count('<project')} AOSP projects")
PY

echo "==> validating"
"$ROOT/tools/validate.py"

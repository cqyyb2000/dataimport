#!/usr/bin/env bash
# 有网 Linux：下载 manylinux / 本机平台 wheel，默认输出到 offline_packages_linux
# 用法（在 backend 目录）: bash scripts/download_offline_deps.sh
set -euo pipefail
cd "$(dirname "$0")/.."

DEST="${1:-offline_packages_linux}"
rm -rf "${DEST}.tmp"
mkdir -p "${DEST}.tmp"

python3 -m pip install -U pip wheel
python3 -m pip download -r requirements.txt -d "${DEST}.tmp"
python3 -m pip download pip setuptools wheel -d "${DEST}.tmp"

mkdir -p "$DEST"
rm -f "$DEST"/*.whl "$DEST"/*.tar.gz 2>/dev/null || true
cp -a "${DEST}.tmp/." "$DEST/"
rm -rf "${DEST}.tmp"

# ASCII requirements
grep -v '^\s*#' requirements.txt | grep -v '^\s*$' > "$DEST/requirements-offline.txt"
echo "pip install --no-index --find-links=. -r requirements-offline.txt" > "$DEST/install_requirements.txt"

echo "Done: $DEST ($(ls -1 "$DEST"/*.whl 2>/dev/null | wc -l) wheels)"
echo "Offline install:"
echo "  python3 -m venv venv && . venv/bin/activate"
echo "  pip install --no-index --find-links=$DEST -r $DEST/requirements-offline.txt"

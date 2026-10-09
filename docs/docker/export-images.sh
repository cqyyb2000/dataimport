#!/usr/bin/env bash
# 在有网的 Linux / WSL 上构建并导出镜像
# 用法：在 docs/docker 目录执行  bash export-images.sh
set -euo pipefail
cd "$(dirname "$0")"

OUT_DIR="./offline-bundle/02-images"
mkdir -p "$OUT_DIR"
export DOCKER_DEFAULT_PLATFORM="${DOCKER_DEFAULT_PLATFORM:-linux/amd64}"

echo "==> pull mysql:8.0"
docker pull mysql:8.0

echo "==> build backend + nginx"
docker compose build

echo "==> save images"
docker save -o "$OUT_DIR/mysql-8.0.tar" mysql:8.0
docker save -o "$OUT_DIR/dataimport-backend.tar" dataimport-backend:latest
docker save -o "$OUT_DIR/dataimport-nginx.tar" dataimport-nginx:latest

ls -lh "$OUT_DIR"
echo "Done. On Ubuntu: docker load -i <file>.tar"
echo "Then: docker compose -f docker-compose.offline.yml up -d"

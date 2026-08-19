#!/usr/bin/env bash
# ============================================================
# 03-deploy-frontend.sh - 前端部署（幂等，可重复执行）
# 功能：将本地构建好的 dist/ 部署到 Nginx 托管目录
# 用法：bash 03-deploy-frontend.sh [/path/to/dist]
#   不传参数时默认使用 /tmp/cacch-frontend-dist
#   （本地 Windows 构建：cd web-frontend && npm run build）
# ============================================================
set -euo pipefail

APP_USER="aidoc"
APP_DIR="/home/aidoc/cacch-ai-platform"
FRONTEND_DIR="$APP_DIR/frontend-dist"

SRC_DIR="${1:-/tmp/cacch-frontend-dist}"

if [[ ! -d "$SRC_DIR" ]]; then
    echo "[ERROR] 未找到构建产物: $SRC_DIR"
    echo "        请先在本地构建：cd web-frontend && npm install && npm run build"
    echo "        再上传：scp -r web-frontend/dist aidoc@10.80.85.85:/tmp/cacch-frontend-dist"
    exit 1
fi

echo "==> [1/2] 校验构建产物"
if [[ ! -f "$SRC_DIR/index.html" ]]; then
    echo "[ERROR] $SRC_DIR 中未找到 index.html，不是有效的 Vite 构建产物"
    exit 1
fi

echo "==> [2/2] 部署到 $FRONTEND_DIR"
# 先放临时目录再原子切换，避免更新中断导致页面 404
STAGING_DIR="$APP_DIR/frontend-dist.new"
rm -rf "$STAGING_DIR"
cp -r "$SRC_DIR" "$STAGING_DIR"
chown -R "$APP_USER":"$APP_USER" "$STAGING_DIR"

# 原子切换
rm -rf "$FRONTEND_DIR.old"
if [[ -d "$FRONTEND_DIR" ]]; then
    mv "$FRONTEND_DIR" "$FRONTEND_DIR.old"
fi
mv "$STAGING_DIR" "$FRONTEND_DIR"
rm -rf "$FRONTEND_DIR.old"

echo "    文件数: $(find "$FRONTEND_DIR" -type f | wc -l)"
echo ""
echo "[OK] 前端部署完成（静态文件即时生效，无需重启 Nginx）"
echo "    访问: http://10.80.85.85"

#!/usr/bin/env bash
# ============================================================
# deploy-all.sh - 一键部署（初始化 + 后端 + Nginx）
# 用法：sudo bash deploy-all.sh [frontend_dist_path]
#   frontend_dist_path 可选；不传则跳过前端部署
# 注意：03-deploy-frontend.sh 不需要 sudo，可单独以 aidoc 执行
# ============================================================
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo "########## [1/4] 环境初始化 ##########"
sudo bash "$SCRIPT_DIR/01-init-server.sh"

echo "########## [2/4] 后端部署 ##########"
sudo bash "$SCRIPT_DIR/02-deploy-backend.sh"

if [[ $# -ge 1 && -d "$1" ]]; then
    echo "########## [3/4] 前端部署 ##########"
    sudo bash "$SCRIPT_DIR/03-deploy-frontend.sh" "$1"
else
    echo "########## [3/4] 前端部署（跳过：未提供 dist 路径）##########"
    echo "       可稍后执行：bash $SCRIPT_DIR/03-deploy-frontend.sh <dist路径>"
fi

echo "########## [4/4] Nginx 配置 ##########"
sudo bash "$SCRIPT_DIR/04-setup-nginx.sh"

echo ""
echo "===== 部署完成 ====="
echo "前端:   http://10.80.85.85"
echo "健康:   http://10.80.85.85/api/v1/health"
echo "日志:   journalctl -u cacch-ai -f"
echo "配置:   请检查 /home/aidoc/cacch-ai-platform/.env 中的密钥"

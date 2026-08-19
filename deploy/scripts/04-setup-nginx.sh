#!/usr/bin/env bash
# ============================================================
# 04-setup-nginx.sh - Nginx 配置安装（幂等，跨平台）
# 功能：安装站点配置、移除/备份默认站点、测试并重载 Nginx
# 用法：sudo bash 04-setup-nginx.sh
# ============================================================
set -euo pipefail

APP_DIR="/home/aidoc/cacch-ai-platform"
SRC_CONF="$APP_DIR/deploy/config/nginx-cacch.conf"

if [[ $EUID -ne 0 ]]; then
    echo "[ERROR] 请使用 root 执行：sudo bash $0"
    exit 1
fi

if [[ ! -f "$SRC_CONF" ]]; then
    echo "[ERROR] 未找到 $SRC_CONF"
    echo "        请确认项目代码已上传到 $APP_DIR"
    exit 1
fi

# --- 检测操作系统，选择 Nginx 配置目录 ---
if [[ -f /etc/os-release ]]; then
    source /etc/os-release
fi
OS_ID="${ID:-unknown}"
OS_LIKE="${ID_LIKE:-}"

IS_DEBIAN=0
if [[ "$OS_ID" == "debian" || "$OS_ID" == "ubuntu" || "$OS_LIKE" == *"debian"* ]]; then
    IS_DEBIAN=1
fi

if [[ $IS_DEBIAN -eq 1 ]]; then
    echo "==> [1/4] 安装站点配置（Debian/Ubuntu 风格）"
    AVAILABLE="/etc/nginx/sites-available/cacch-ai"
    ENABLED="/etc/nginx/sites-enabled/cacch-ai"
    cp "$SRC_CONF" "$AVAILABLE"
    ln -sf "$AVAILABLE" "$ENABLED"

    echo "==> [2/4] 移除默认站点（避免 80 端口冲突）"
    rm -f /etc/nginx/sites-enabled/default
else
    echo "==> [1/4] 安装站点配置（RHEL/Rocky/CentOS 风格）"
    cp "$SRC_CONF" /etc/nginx/conf.d/cacch-ai.conf

    echo "==> [2/4] 备份默认站点（避免 80 端口冲突）"
    if [[ -f /etc/nginx/conf.d/default.conf ]]; then
        mv /etc/nginx/conf.d/default.conf "/etc/nginx/conf.d/default.conf.bak.$(date +%s)"
        echo "    已备份 /etc/nginx/conf.d/default.conf"
    fi
    # 某些版本默认配置在 /etc/nginx/nginx.conf 的 server 块，不影响 conf.d，按发行版默认处理即可
fi

echo "==> [3/4] 检查前端目录存在"
if [[ ! -f "$APP_DIR/frontend-dist/index.html" ]]; then
    echo "    [WARN] frontend-dist 尚无 index.html，请先执行 03-deploy-frontend.sh"
fi

echo "==> [4/4] 测试并重载 Nginx"
if nginx -t; then
    systemctl enable nginx
    systemctl restart nginx
    echo "    [OK] Nginx 已重载"
else
    echo "    [ERROR] Nginx 配置测试失败，请检查站点配置"
    exit 1
fi

echo ""
echo "[OK] Nginx 配置完成"
echo "    访问: http://10.80.85.85  （前端页面）"
echo "    API:  http://10.80.85.85/api/v1/health"

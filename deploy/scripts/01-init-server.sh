#!/usr/bin/env bash
# ============================================================
# 01-init-server.sh - 服务器环境初始化（幂等，跨平台）
# 功能：安装 Python 3.12、venv、pip、Nginx，创建目录结构
# 适用：Ubuntu / Debian / Rocky / RHEL / CentOS / AlmaLinux / openEuler
# 用法：sudo bash 01-init-server.sh
# ============================================================
set -euo pipefail

APP_USER="aidoc"
APP_DIR="/home/aidoc/cacch-ai-platform"

# --- 检查 root ---
if [[ $EUID -ne 0 ]]; then
    echo "[ERROR] 请使用 root 执行：sudo bash $0"
    exit 1
fi

# --- 检测操作系统 ---
if [[ ! -f /etc/os-release ]]; then
    echo "[ERROR] 无法检测操作系统（缺少 /etc/os-release）"
    exit 1
fi
source /etc/os-release
OS_ID="${ID:-unknown}"
OS_LIKE="${ID_LIKE:-}"

IS_DEBIAN=0
IS_RHEL=0
PKG_MGR=""

case "$OS_ID" in
    debian|ubuntu)
        IS_DEBIAN=1
        PKG_MGR="apt-get"
        ;;
    rocky|centos|rhel|almalinux|oracle|fedora|ol|anolis|openeuler)
        IS_RHEL=1
        PKG_MGR="dnf"
        ;;
    *)
        if [[ "$OS_LIKE" == *"debian"* ]]; then
            IS_DEBIAN=1
            PKG_MGR="apt-get"
        elif [[ "$OS_LIKE" == *"rhel"* || "$OS_LIKE" == *"centos"* || "$OS_LIKE" == *"fedora"* ]]; then
            IS_RHEL=1
            PKG_MGR="dnf"
        else
            echo "[ERROR] 不支持的操作系统: $OS_ID (ID_LIKE: $OS_LIKE)"
            echo "        本脚本支持 Debian/Ubuntu/Rocky/RHEL/CentOS/AlmaLinux/openEuler"
            exit 1
        fi
        ;;
esac

echo "==> 检测到系统: $OS_ID，使用包管理器: $PKG_MGR"

# --- 检查/安装 Python 3.12 ---
PYTHON_BIN=""
if command -v python3.12 >/dev/null 2>&1; then
    PYTHON_BIN="python3.12"
    echo "    发现 python3.12，直接使用"
elif command -v python3 >/dev/null 2>&1; then
    PY_VER=$(python3 -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')
    echo "    当前 python3: $PY_VER"
    major=${PY_VER%%.*}
    minor=${PY_VER##*.}
    if [[ $major -ge 3 && $minor -ge 12 ]]; then
        PYTHON_BIN="python3"
    fi
fi

if [[ -z "$PYTHON_BIN" ]]; then
    echo "==> 安装 Python 3.12 ..."
    if [[ $IS_DEBIAN -eq 1 ]]; then
        export DEBIAN_FRONTEND=noninteractive
        apt-get update -y
        apt-get install -y software-properties-common
        add-apt-repository -y ppa:deadsnakes/ppa
        apt-get update -y
        apt-get install -y python3.12 python3.12-venv python3.12-dev
    else
        # Rocky/RHEL/CentOS/Alma/openEuler
        $PKG_MGR install -y epel-release || true
        $PKG_MGR install -y python3.12 python3.12-pip python3.12-devel
        # 确保 venv 有 pip（某些精简镜像可能缺少）
        python3.12 -m ensurepip --upgrade || true
    fi
    PYTHON_BIN="python3.12"
fi

echo "    使用解释器: $PYTHON_BIN"

# --- 安装系统依赖 ---
echo "==> 安装依赖（venv / pip / nginx / 基础工具 / PostgreSQL 开发库）"
if [[ $IS_DEBIAN -eq 1 ]]; then
    export DEBIAN_FRONTEND=noninteractive
    apt-get update -y
    apt-get install -y \
        "$PYTHON_BIN"-venv \
        "$PYTHON_BIN"-pip \
        nginx \
        curl \
        git \
        build-essential \
        libpq-dev
else
    $PKG_MGR install -y epel-release || true
    $PKG_MGR install -y \
        "$PYTHON_BIN" \
        python3.12-pip \
        python3.12-devel \
        nginx \
        curl \
        git \
        gcc \
        libpq-devel
fi

# --- 创建应用目录结构 ---
echo "==> 创建应用目录结构"
mkdir -p "$APP_DIR"/{logs,data/crawl,frontend-dist,deploy}
chown -R "$APP_USER":"$APP_USER" "$APP_DIR"

# --- Rocky/RHEL 系：处理 SELinux，允许 Nginx 读取用户目录 ---
if [[ $IS_RHEL -eq 1 ]] && command -v setsebool >/dev/null 2>&1; then
    echo "==> 配置 SELinux（如有启用），允许 Nginx 读取用户内容"
    setsebool -P httpd_read_user_content 1 2>/dev/null || true
fi

# --- 确认版本 ---
echo "==> 确认 nginx 与 python 版本"
nginx -v 2>&1 || true
"$PYTHON_BIN" --version

echo ""
echo "[OK] 环境初始化完成。下一步：bash 02-deploy-backend.sh"

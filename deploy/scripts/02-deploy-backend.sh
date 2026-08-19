#!/usr/bin/env bash
# ============================================================
# 02-deploy-backend.sh - 后端部署（幂等，可重复执行）
# 功能：创建 venv、安装依赖、写入 .env、注册 systemd 服务
# 用法：bash 02-deploy-backend.sh
#   （需已执行 01-init-server.sh；以 aidoc 用户或 root 均可）
# ============================================================
set -euo pipefail

APP_USER="aidoc"
APP_DIR="/home/aidoc/cacch-ai-platform"
DEPLOY_DIR="$APP_DIR/deploy"
VENV_DIR="$APP_DIR/.venv"
ENV_FILE="$APP_DIR/.env"

if [[ $EUID -eq 0 ]]; then
    RUNNER="sudo -u $APP_USER"
else
    RUNNER=""
fi

# 选择 Python 解释器（与 01-init 保持一致：优先 python3.12）
if command -v python3.12 >/dev/null 2>&1; then
    PYTHON_BIN="python3.12"
else
    PYTHON_BIN="python3"
fi

echo "==> [1/5] 检查项目文件是否已上传"
if [[ ! -f "$APP_DIR/pyproject.toml" ]]; then
    echo "[ERROR] 未找到 $APP_DIR/pyproject.toml"
    echo "        请先从本地将项目代码上传到服务器（见 README.md 第 3 步）"
    exit 1
fi

echo "==> [2/5] 创建 Python 虚拟环境"
if [[ ! -d "$VENV_DIR" ]]; then
    $PYTHON_BIN -m venv "$VENV_DIR"
    echo "    已创建 $VENV_DIR ($PYTHON_BIN)"
else
    echo "    venv 已存在，跳过"
fi
chown -R "$APP_USER":"$APP_USER" "$VENV_DIR" 2>/dev/null || true

echo "==> [3/5] 安装后端依赖（pyproject.toml + gunicorn）"
$RUNNER "$VENV_DIR/bin/pip" install --upgrade pip
$RUNNER "$VENV_DIR/bin/pip" install "gunicorn>=22.0.0"
$RUNNER "$VENV_DIR/bin/pip" install -e "$APP_DIR"

echo "==> [4/5] 写入生产环境配置 .env"
if [[ -f "$ENV_FILE" ]]; then
    echo "    .env 已存在，跳过（如需重新生成请手动删除）"
else
    cp "$DEPLOY_DIR/config/.env.production" "$ENV_FILE"
    chown "$APP_USER":"$APP_USER" "$ENV_FILE"
    echo "    已从模板生成 $ENV_FILE"
    echo "    [WARN] 请编辑 $ENV_FILE 修改："
    echo "           API_AUTH_TOKEN / AUTH_TOKEN_SECRET / LLM_API_KEY / DATABASE_URL"
fi

echo "==> [5/5] 注册并启动 systemd 服务"
cp "$DEPLOY_DIR/config/cacch-ai.service" /etc/systemd/system/cacch-ai.service
systemctl daemon-reload
systemctl enable cacch-ai
systemctl restart cacch-ai

echo "    等待服务启动（最多 60 秒）..."
for i in $(seq 1 60); do
    if curl -sf http://127.0.0.1:8000/api/v1/health >/dev/null 2>&1; then
        echo "    [OK] 后端健康检查通过: http://127.0.0.1:8000/api/v1/health"
        break
    fi
    if [[ $i -eq 60 ]]; then
        echo "    [WARN] 健康检查未通过，请查看日志："
        echo "           journalctl -u cacch-ai -n 50 --no-pager"
        echo "           tail -n 50 /home/aidoc/cacch-ai-platform/logs/gunicorn-error.log"
        exit 1
    fi
    sleep 1
done

systemctl status cacch-ai --no-pager | head -n 8 || true
echo ""
echo "[OK] 后端部署完成。下一步：bash 03-deploy-frontend.sh <dist路径>"

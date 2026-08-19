# CACCH AI 平台 - 生产部署指南（方案 B：裸金属 / 2C4G）

> 目标服务器：`10.80.85.85`（2C4G，Ubuntu 22.04+）
> 用户：`aidoc` ｜ 安装根目录：`/home/aidoc`
> 方式：**前端静态资源由 Nginx 托管，后端 FastAPI 由 Gunicorn + systemd 托管，前后端独立部署、互不影响**

```
浏览器 ──> Nginx(:80) ──┬──> 前端静态资源  /home/aidoc/cacch-ai-platform/frontend-dist
                       └──> /api/ 反代 ──> Gunicorn(127.0.0.1:8000) ──> PostgreSQL(外部)
                                                       │
                                                       └──> DashScope LLM API
```

---

## 一、本地准备（Windows 开发机）

### 1. 构建前端（产出 dist/）

```bash
cd web-frontend
npm install
npm run build
# 产物在 web-frontend/dist/
```

### 2. 上传项目代码到服务器

```bash
# 需要排除：node_modules / .venv / dist / __pycache__ / .git
scp -r \
  --exclude node_modules --exclude .venv --exclude dist \
  --exclude __pycache__ --exclude .git --exclude data \
  . aidoc@10.80.85.85:/home/aidoc/cacch-ai-platform/
```

> 如果服务器还没有 `cacch-ai-platform` 目录，先 `ssh aidoc@10.80.85.85 "mkdir -p /home/aidoc/cacch-ai-platform"`。
> Windows 的 scp 不支持 `--exclude`，可用 rsync（Git Bash 自带）：
> ```bash
> rsync -avz --exclude node_modules --exclude .venv --exclude dist \
>   --exclude __pycache__ --exclude .git --exclude data \
>   ./ aidoc@10.80.85.85:/home/aidoc/cacch-ai-platform/
> ```

### 3. 上传前端构建产物

```bash
scp -r web-frontend/dist aidoc@10.80.85.85:/tmp/cacch-frontend-dist
```

---

## 二、服务器部署（按顺序执行）

```bash
# SSH 登录
ssh aidoc@10.80.85.85
cd /home/aidoc/cacch-ai-platform

# 1. 环境初始化（安装 Python 3.12 / venv / Nginx）—— 需要 sudo
sudo bash deploy/scripts/01-init-server.sh

# 2. 后端部署（venv + 依赖 + systemd 服务）
bash deploy/scripts/02-deploy-backend.sh

# 3. 前端部署（把刚才上传的 dist 放到位）
bash deploy/scripts/03-deploy-frontend.sh /tmp/cacch-frontend-dist

# 4. Nginx 配置并启动 —— 需要 sudo
sudo bash deploy/scripts/04-setup-nginx.sh
```

> 也可以一条命令完成 1/2/4（前端需自行传 dist）：
> ```bash
> sudo bash deploy/scripts/deploy-all.sh /tmp/cacch-frontend-dist
> ```

---

## 三、必改配置（重要）

部署脚本会把 `deploy/config/.env.production` 拷贝为 `/home/aidoc/cacch-ai-platform/.env`，**首次部署后必须修改**：

```bash
nano /home/aidoc/cacch-ai-platform/.env
```

| 变量 | 说明 | 必须改 |
|------|------|--------|
| `API_AUTH_TOKEN` | API 鉴权 token，`openssl rand -hex 32` 生成 | ✅ |
| `AUTH_TOKEN_SECRET` | 用户 token 签名密钥，同上 | ✅ |
| `LLM_API_KEY` | DashScope（阿里云百炼）API Key | ✅ |
| `DATABASE_URL` | 生产 PostgreSQL 地址（默认指 10.80.86.93） | 按实际 |
| `CORS_ORIGINS` | 如需多域名访问，逗号分隔 | 可选 |

改完重启后端：

```bash
sudo systemctl restart cacch-ai
```

---

## 四、验证

```bash
# 1. 后端健康检查（直连）
curl http://127.0.0.1:8000/api/v1/health
# 期望: {"code":0,"message":"ok","data":{"status":"ok"}}

# 2. 通过 Nginx 访问（经反向代理）
curl http://10.80.85.85/api/v1/health

# 3. 浏览器打开
#    http://10.80.85.85
```

---

## 五、日常运维

### 服务管理

```bash
sudo systemctl status cacch-ai      # 查看状态
sudo systemctl restart cacch-ai     # 重启后端
sudo journalctl -u cacch-ai -f      # 实时日志
tail -f /home/aidoc/cacch-ai-platform/logs/gunicorn-error.log  # gunicorn 日志
```

### 升级后端

```bash
# 1. 本地提交新代码并推送
# 2. 服务器拉取/上传后：
sudo bash /home/aidoc/cacch-ai-platform/deploy/scripts/02-deploy-backend.sh
```

### 升级前端（独立，不影响后端）

```bash
# 本地
cd web-frontend && npm run build
scp -r web-frontend/dist aidoc@10.80.85.85:/tmp/cacch-frontend-dist

# 服务器
bash /home/aidoc/cacch-ai-platform/deploy/scripts/03-deploy-frontend.sh /tmp/cacch-frontend-dist
# 静态文件原子切换，无需重启任何服务
```

### 防火墙

```bash
sudo ufw allow 80/tcp
sudo ufw allow 22/tcp
sudo ufw enable
```

---

## 六、文件清单

```
deploy/
├── README.md                         # 本指南
├── config/
│   ├── .env.production               # 生产环境变量模板（拷贝为 .env）
│   ├── gunicorn.conf.py              # Gunicorn 配置（2 workers，2C4G 优化）
│   ├── cacch-ai.service              # systemd 单元文件
│   └── nginx-cacch.conf              # Nginx 站点配置（SPA + API 反代）
└── scripts/
    ├── 01-init-server.sh             # 环境初始化（幂等）
    ├── 02-deploy-backend.sh          # 后端部署（幂等）
    ├── 03-deploy-frontend.sh         # 前端部署（幂等）
    ├── 04-setup-nginx.sh             # Nginx 配置（幂等）
    └── deploy-all.sh                 # 一键部署 1+2+4
```

所有脚本均**幂等**（可重复执行），重复执行不会破坏现有部署。

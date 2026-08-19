# 本地一键打包部署

在**开发机**上运行一个命令，自动完成：前端构建 → 代码打包 → 上传服务器 → 远程部署（后端 + 前端 + Nginx）→ 健康检查。

## 快速开始

```bash
# 一键全量部署（首次部署，含服务器环境初始化）
python deploy/local/deploy-local.py

# 日常更新部署（服务器已初始化过，跳过 init 省时间）
python deploy/local/deploy-local.py --skip-init
```

> Windows 下若 `python` 不在 PATH，用完整路径：
> `C:\Users\Administrator\.workbuddy\binaries\python\versions\3.13.12\python.exe deploy/local/deploy-local.py`
> （依赖 paramiko，未安装会自动提示 `pip install paramiko`）

## 常用参数

| 参数 | 说明 |
|------|------|
| `--host H --user U --password P --port N` | 目标服务器（默认 `10.80.85.85 / aidoc / aidoc / 22`） |
| `--skip-init` | 跳过环境初始化（已初始化过用这个，节省 2-5 分钟） |
| `--skip-build` | 跳过前端构建，复用本地已有 `web-frontend/dist` |
| `--only-package` | 只打包不上传，产物在 `deploy/local/packages/` |
| `--exclude-data` | 打包不含 `data/`（默认包含，12MB） |

## 流程说明

```
[本地] npm run build ──> web-frontend/dist
       │
       ├─ 打包 tar.gz（app/ + pyproject.toml + data/ + deploy/ + scripts/
       │              + web-frontend 源码 + dist-build）
       │   ├─ 自动排除 node_modules / __pycache__ / .pyc / .env* / .git
       │   └─ 产物: deploy/local/packages/cacch-package-<时间戳>.tar.gz (~7MB)
       │
       └─ SFTP 上传到服务器 /tmp/cacch-deploy/
              │
              └─ [远程] 解压 -> /home/aidoc/cacch-ai-platform/
                     ├─ 01-init-server.sh  环境初始化（apt 装 Python3.12/Nginx，需 sudo）
                     ├─ 02-deploy-backend.sh  后端部署（venv + pip install + systemd）
                     ├─ 03-deploy-frontend.sh <dist>  前端原子切换
                     ├─ 04-setup-nginx.sh  Nginx 站点配置（需 sudo）
                     └─ 健康检查: /api/v1/health + 前端首页
```

## 首次部署后的必做项

脚本执行完后，到服务器上修改 `.env` 中的密钥并重启服务：

```bash
ssh aidoc@10.80.85.85
sudo nano /home/aidoc/cacch-ai-platform/.env
# 修改: API_AUTH_TOKEN / AUTH_TOKEN_SECRET（用 openssl rand -hex 32 生成）
# 修改: LLM_API_KEY / LLM_MODEL / DATABASE_URL（按生产环境填写）
sudo systemctl restart cacch-ai
```

## 注意事项

1. **sudo 密码**：脚本用 SSH 密码自动执行 sudo（01/04 两步需要 root）。若 aidoc 不在 sudoers 中，会失败，需先手动 `ssh` 配置：`sudo usermod -aG sudo aidoc`
2. **前端在本地构建**：服务器 2C4G 未装 Node，前端由本地 `npm run build` 构建后以 dist 形式上传（符合资源优化）
3. **幂等**：重复执行不会重复安装/覆盖 .env，可放心重跑
4. **网络要求**：开发机需能直连服务器 22 端口；apt 安装依赖时服务器需能访问外网

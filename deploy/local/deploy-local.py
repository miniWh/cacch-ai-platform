#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
cacch-ai-platform 本地一键打包部署脚本
=====================================
在开发机（Windows/Linux/macOS 均可）运行：构建前端 -> 打包 -> 上传 -> 远程部署 -> 健康检查。

默认部署目标:
    服务器: 10.80.85.85  (2C4G, Ubuntu)
    用户:   aidoc
    根目录: /home/aidoc/cacch-ai-platform

用法:
    python deploy/local/deploy-local.py                      # 一键全量部署（默认密码 aidoc）
    python deploy/local/deploy-local.py --password 'xxx'     # 指定 SSH/sudo 密码
    python deploy/local/deploy-local.py --skip-init          # 跳过环境初始化（已初始化过）
    python deploy/local/deploy-local.py --skip-build         # 跳过前端构建（复用已有 dist）
    python deploy/local/deploy-local.py --only-package       # 只打包不上传（包在 deploy/local/packages/）
    python deploy/local/deploy-local.py --exclude-data       # 打包时不包含 data/ 目录
    python deploy/local/deploy-local.py --host H --user U --password P --port 22

依赖: paramiko（未安装会自动提示安装命令）
"""

import argparse
import os
import shlex
import shutil
import subprocess
import sys
import tarfile
import time

# ---------------------------------------------------------------------------
# 常量
# ---------------------------------------------------------------------------
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.normpath(os.path.join(SCRIPT_DIR, "..", ".."))
FE_DIR = os.path.join(PROJECT_ROOT, "web-frontend")
PKG_OUT_DIR = os.path.join(SCRIPT_DIR, "packages")
PKG_ROOT_NAME = "cacch-package"

REMOTE_TMP = "/tmp/cacch-deploy"
REMOTE_PKG = REMOTE_TMP + "/package.tar.gz"
REMOTE_EXTRACT = REMOTE_TMP + "/extract"
REMOTE_DIST = REMOTE_TMP + "/dist-build"
REMOTE_APP_DIR = "/home/aidoc/cacch-ai-platform"

# 打包时排除的目录名（任意层级）
EXCLUDE_DIR_NAMES = {
    "__pycache__", "node_modules", ".venv", "venv", ".git", ".idea",
    ".workbuddy", "packages", "dist", ".pytest_cache", ".mypy_cache",
    ".ruff_cache", "__screenshots__", ".turbo",
}
# 打包时排除的文件名规则
EXCLUDE_FILE_NAMES = (
    ".pyc", ".pyo", ".log", ".tar.gz", ".tmp", ".DS_Store", ".env",
)
EXCLUDE_FILE_START = (".env",)  # .env.development / .env.production 等


# ---------------------------------------------------------------------------
# 工具函数
# ---------------------------------------------------------------------------
def log(msg):
    print(f"[{time.strftime('%H:%M:%S')}] {msg}", flush=True)


def find_node():
    """返回 (node可执行文件, npm-cli.js路径)；找不到返回 (None, None)。"""
    node_exe = shutil.which("node")
    if not node_exe and os.name == "nt":
        # 兜底：WorkBuddy managed node
        managed = r"C:\Users\Administrator\.workbuddy\binaries\node\versions\22.22.2\node.exe"
        if os.path.exists(managed):
            node_exe = managed
    if not node_exe:
        return None, None
    node_dir = os.path.dirname(node_exe)
    npm_cli = os.path.join(node_dir, "node_modules", "npm", "bin", "npm-cli.js")
    if not os.path.exists(npm_cli):
        return node_exe, None
    return node_exe, npm_cli


def build_frontend():
    """本地构建前端（npm run build），产出 web-frontend/dist。"""
    if not os.path.isdir(FE_DIR):
        log("[ERROR] 未找到前端目录: %s" % FE_DIR)
        sys.exit(1)
    if not os.path.isdir(os.path.join(FE_DIR, "node_modules")):
        log("==> node_modules 不存在，先执行 npm install（首次较慢）...")
        subprocess.run("npm install", shell=True, cwd=FE_DIR, check=True)
    node_exe, npm_cli = find_node()
    if not node_exe:
        log("[ERROR] 未找到 node/npm，请先安装 Node.js 或加入 PATH")
        sys.exit(1)
    if npm_cli:
        log("==> 执行: %s %s run build" % (node_exe, npm_cli))
        subprocess.run([node_exe, npm_cli, "run", "build"], cwd=FE_DIR, check=True)
    else:
        log("==> 执行: npm run build")
        subprocess.run("npm run build", shell=True, cwd=FE_DIR, check=True)
    dist_dir = os.path.join(FE_DIR, "dist")
    if not os.path.isfile(os.path.join(dist_dir, "index.html")):
        log("[ERROR] 构建完成但 dist/index.html 不存在，构建可能失败")
        sys.exit(1)
    log("前端构建完成: %s" % dist_dir)


# ---------------------------------------------------------------------------
# 打包
# ---------------------------------------------------------------------------
def _should_skip_dir(name):
    return name in EXCLUDE_DIR_NAMES


def _should_skip_file(name):
    if name.endswith(EXCLUDE_FILE_NAMES):
        return True
    for prefix in EXCLUDE_FILE_START:
        if name.startswith(prefix):
            return True
    return False


def _add_dir(tar, src_dir, arc_root):
    """把 src_dir 递归加入 tar，arc_root 为包内目标目录（如 'cacch-package/app'）。"""
    for root, dirs, files in os.walk(src_dir):
        dirs[:] = [d for d in dirs if not _should_skip_dir(d)]
        for f in files:
            if _should_skip_file(f):
                continue
            full = os.path.join(root, f)
            rel = os.path.relpath(full, src_dir)
            arc = os.path.join(arc_root, rel).replace(os.sep, "/")
            try:
                tar.add(full, arcname=arc, recursive=False)
            except OSError as e:
                log("  [WARN] 跳过 %s: %s" % (full, e))


def make_package(exclude_data=False):
    """生成 tar.gz 包，返回包路径。"""
    if not os.path.isfile(os.path.join(PROJECT_ROOT, "pyproject.toml")):
        log("[ERROR] 项目根缺少 pyproject.toml，请确认在 %s 下运行" % PROJECT_ROOT)
        sys.exit(1)

    os.makedirs(PKG_OUT_DIR, exist_ok=True)
    ts = time.strftime("%Y%m%d-%H%M%S")
    pkg_path = os.path.join(PKG_OUT_DIR, "cacch-package-%s.tar.gz" % ts)

    log("==> 开始打包 -> %s" % pkg_path)
    n_files = 0

    with tarfile.open(pkg_path, "w:gz") as tar:
        # 1) 后端核心
        _add_dir(tar, os.path.join(PROJECT_ROOT, "app"), PKG_ROOT_NAME + "/app")
        tar.add(os.path.join(PROJECT_ROOT, "pyproject.toml"),
                arcname=PKG_ROOT_NAME + "/pyproject.toml")

        # 2) 数据目录（可跳过）
        if exclude_data:
            log("  [SKIP] data/ 已排除 (--exclude-data)")
        else:
            _add_dir(tar, os.path.join(PROJECT_ROOT, "data"), PKG_ROOT_NAME + "/data")

        # 3) 部署脚本与配置
        _add_dir(tar, os.path.join(PROJECT_ROOT, "deploy"), PKG_ROOT_NAME + "/deploy")
        _add_dir(tar, os.path.join(PROJECT_ROOT, "scripts"), PKG_ROOT_NAME + "/scripts")

        # 4) 前端源码（排除 node_modules/dist/.env*）
        _add_dir(tar, FE_DIR, PKG_ROOT_NAME + "/web-frontend")

        # 5) 前端构建产物 -> dist-build（供 03-deploy-frontend.sh 使用）
        dist_dir = os.path.join(FE_DIR, "dist")
        if os.path.isdir(dist_dir):
            _add_dir(tar, dist_dir, PKG_ROOT_NAME + "/dist-build")
            log("  dist/ 已打包为 dist-build/")
        else:
            log("  [WARN] 未找到 %s，包内不含前端构建产物" % dist_dir)

    size_mb = os.path.getsize(pkg_path) / 1024 / 1024
    log("打包完成: %.1f MB" % size_mb)
    return pkg_path


# ---------------------------------------------------------------------------
# 远程部署（paramiko）
# ---------------------------------------------------------------------------
def _import_paramiko():
    try:
        import paramiko  # noqa
        return paramiko
    except ImportError:
        log("[ERROR] 未安装 paramiko，请先安装：")
        log("    pip install paramiko")
        sys.exit(1)


def run_cmd(client, cmd, timeout=900, sudo=False, password="", label=None):
    """远程执行命令，实时打印输出，返回 (exit_code, 输出文本)。"""
    if label:
        log("==> %s" % label)
    log("$ %s" % cmd)
    if sudo:
        cmd = "echo %s | sudo -S -p '' %s" % (shlex.quote(password), cmd)
    stdin, stdout, stderr = client.exec_command(cmd, timeout=timeout, get_pty=True)
    out_lines = []
    for line in iter(stdout.readline, ""):
        sys.stdout.write(line)
        sys.stdout.flush()
        out_lines.append(line)
    err = stderr.read().decode("utf-8", "ignore")
    if err.strip():
        sys.stdout.write(err)
    rc = stdout.channel.recv_exit_status()
    if rc != 0:
        log("[WARN] 命令退出码: %d" % rc)
    return rc, "".join(out_lines)


def deploy_remote(pkg_path, host, user, password, port, skip_init):
    """上传包并远程执行部署，返回最终是否成功。"""
    paramiko = _import_paramiko()

    log("==> 连接服务器 %s:%s (%s) ..." % (host, port, user))
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    try:
        client.connect(host, port=port, username=user, password=password,
                       timeout=20, banner_timeout=30, auth_timeout=30)
    except Exception as e:
        log("[ERROR] 连接失败: %s" % e)
        sys.exit(1)
    log("连接成功")

    # 1) 确保远程临时目录存在并清理旧数据（上传前必须先建目录）
    rc, _ = run_cmd(
        client,
        "rm -rf %s %s %s && mkdir -p %s" % (REMOTE_PKG, REMOTE_EXTRACT, REMOTE_DIST, REMOTE_TMP),
        timeout=60, label="准备远程临时目录 %s" % REMOTE_TMP,
    )
    if rc != 0:
        log("[ERROR] 无法创建远程临时目录，中止部署")
        client.close()
        sys.exit(1)

    # 2) 上传包
    log("==> 上传 %s -> %s" % (pkg_path, REMOTE_PKG))
    sftp = client.open_sftp()
    try:
        sftp.put(pkg_path, REMOTE_PKG)
    finally:
        sftp.close()
    log("上传完成")

    # 3) 远程解压 + 拷贝到应用目录
    rc, _ = run_cmd(
        client,
        "rm -rf %s %s && mkdir -p %s && tar -xzf %s -C %s && "
        "mv %s/%s/dist-build %s && "
        "cp -a %s/%s/. %s/ && chown -R %s:%s %s"
        % (REMOTE_EXTRACT, REMOTE_DIST, REMOTE_EXTRACT, REMOTE_PKG,
           REMOTE_EXTRACT, REMOTE_EXTRACT, PKG_ROOT_NAME, REMOTE_DIST,
           REMOTE_EXTRACT, PKG_ROOT_NAME, REMOTE_APP_DIR, user, user,
           REMOTE_APP_DIR),
        timeout=300, label="远程解压并拷贝到 %s" % REMOTE_APP_DIR,
    )
    if rc != 0:
        log("[ERROR] 解压/拷贝失败，中止部署")
        client.close()
        sys.exit(1)

    scripts = REMOTE_APP_DIR + "/deploy/scripts"

    # 3) 环境初始化（需 sudo，可选）
    if skip_init:
        log("==> [跳过] 环境初始化 (--skip-init)")
    else:
        rc, _ = run_cmd(
            client,
            "bash %s/01-init-server.sh" % scripts,
            timeout=1200, sudo=True, password=password,
            label="[1/4] 服务器环境初始化（apt 安装 Python3.12/Nginx，首次较慢）",
        )
        if rc != 0:
            log("[ERROR] 初始化失败，请检查服务器日志后重试（可加 --skip-init 跳过此步）")
            client.close()
            sys.exit(1)

    # 4) 后端部署
    rc, _ = run_cmd(
        client,
        "bash %s/02-deploy-backend.sh" % scripts,
        timeout=1200, label="[2/4] 后端部署（venv + 依赖 + systemd 服务）",
    )
    if rc != 0:
        log("[ERROR] 后端部署失败，请查看: journalctl -u cacch-ai -n 50 --no-pager")
        client.close()
        sys.exit(1)

    # 5) 前端部署
    rc, _ = run_cmd(
        client,
        "bash %s/03-deploy-frontend.sh %s" % (scripts, REMOTE_DIST),
        timeout=300, label="[3/4] 前端部署（原子切换 dist）",
    )
    if rc != 0:
        log("[ERROR] 前端部署失败")
        client.close()
        sys.exit(1)

    # 6) Nginx 配置（需 sudo）
    rc, _ = run_cmd(
        client,
        "bash %s/04-setup-nginx.sh" % scripts,
        timeout=300, sudo=True, password=password,
        label="[4/4] Nginx 站点配置",
    )
    if rc != 0:
        log("[ERROR] Nginx 配置失败")
        client.close()
        sys.exit(1)

    # 7) 健康检查
    log("==> 最终健康检查 ...")
    time.sleep(3)
    rc, _ = run_cmd(
        client,
        "curl -sf http://127.0.0.1/api/v1/health && echo && "
        "curl -sf -o /dev/null -w '前端 HTTP 状态: %{http_code}\\n' http://127.0.0.1/",
        timeout=60, label="健康检查（后端 API + 前端页面）",
    )
    client.close()
    if rc != 0:
        log("[WARN] 健康检查未通过，请手动检查服务状态")
        return False
    log("健康检查通过")
    return True


# ---------------------------------------------------------------------------
# main
# ---------------------------------------------------------------------------
def main():
    parser = argparse.ArgumentParser(
        description="cacch-ai-platform 本地一键打包部署",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    parser.add_argument("--host", default="10.80.85.85", help="服务器 IP（默认 10.80.85.85）")
    parser.add_argument("--user", default="aidoc", help="SSH 用户（默认 aidoc）")
    parser.add_argument("--password", default="aidoc", help="SSH/sudo 密码（默认 aidoc，生产务必修改）")
    parser.add_argument("--port", type=int, default=22, help="SSH 端口（默认 22）")
    parser.add_argument("--skip-init", action="store_true", help="跳过服务器环境初始化")
    parser.add_argument("--skip-build", action="store_true", help="跳过前端构建（复用已有 dist）")
    parser.add_argument("--only-package", action="store_true", help="只打包不上传")
    parser.add_argument("--exclude-data", action="store_true", help="打包不包含 data/ 目录")
    args = parser.parse_args()

    log("========== cacch-ai-platform 一键部署 ==========")
    log("目标服务器: %s:%s  用户: %s  应用目录: %s"
        % (args.host, args.port, args.user, REMOTE_APP_DIR))

    # 1) 构建前端
    if args.skip_build:
        log("==> [跳过] 前端构建 (--skip-build)，复用已有 dist")
        if not os.path.isdir(os.path.join(FE_DIR, "dist")):
            log("[ERROR] web-frontend/dist 不存在，无法跳过构建")
            sys.exit(1)
    else:
        build_frontend()

    # 2) 打包
    pkg_path = make_package(exclude_data=args.exclude_data)

    # 3) 只打包模式
    if args.only_package:
        log("========== 打包完成（未上传） ==========")
        log("包路径: %s" % pkg_path)
        log("手动部署: 将包上传到服务器 /tmp 后执行:")
        log("  tar -xzf %s -C /tmp" % os.path.basename(pkg_path))
        log("  sudo bash %s/deploy/scripts/01-init-server.sh" % REMOTE_APP_DIR)
        log("  bash %s/deploy/scripts/02-deploy-backend.sh" % REMOTE_APP_DIR)
        log("  bash %s/deploy/scripts/03-deploy-frontend.sh /tmp/cacch-deploy/dist-build" % REMOTE_APP_DIR)
        log("  sudo bash %s/deploy/scripts/04-setup-nginx.sh" % REMOTE_APP_DIR)
        return

    # 4) 上传 + 远程部署
    ok = deploy_remote(pkg_path, args.host, args.user, args.password,
                       args.port, args.skip_init)

    log("")
    log("========== 部署%s ==========" % ("成功" if ok else "完成（需人工检查）"))
    if ok:
        log("前端:   http://%s" % args.host)
        log("健康:   http://%s/api/v1/health" % args.host)
        log("日志:   ssh %s@%s 'journalctl -u cacch-ai -f'" % (args.user, args.host))
        log("配置:   请检查服务器 %s/.env 中的 API_AUTH_TOKEN / LLM_API_KEY 等密钥" % REMOTE_APP_DIR)


if __name__ == "__main__":
    main()

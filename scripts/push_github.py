# -*- coding: utf-8 -*-
"""
把本地仓库推送到 GitHub。

用法（token 走 stdin 首行或环境变量 GITHUB_TOKEN，绝不写入文件）：
    echo <token> | python push_github.py            # 推送到默认仓库
    echo <token> | python push_github.py --repo account-ops-workbench --owner zhangyanfei6688-hash
    echo <token> | python push_github.py --create   # 仓库不存在时自动创建（私有）

说明：
- token 只会用于本次 HTTP 请求与 git remote URL，不会落地到磁盘；
- 推送完成后会把 remote 里的 token 清掉，remote 改回无凭据的 https 地址。
"""
import argparse
import json
import os
import subprocess
import sys
import urllib.request
import urllib.error

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
API = "https://api.github.com"


def sh(args, cwd=BASE, check=True):
    # git 走本机 http_proxy 会 502（CONNECT tunnel failed），推送必须直连
    env = {k: v for k, v in os.environ.items() if k.lower() not in ("http_proxy", "https_proxy", "all_proxy")}
    p = subprocess.run(args, cwd=cwd, capture_output=True, text=True, encoding="utf-8",
                       errors="replace", env=env)
    if check and p.returncode != 0:
        raise SystemExit("[FAIL] %s\n%s\n%s" % (" ".join(args), p.stdout, p.stderr))
    # git push 的进度信息写 stderr，必须合并返回
    return (p.stdout + "\n" + p.stderr).strip()


def api(method, path, token, payload=None):
    data = json.dumps(payload).encode("utf-8") if payload is not None else None
    req = urllib.request.Request(API + path, data=data, method=method)
    req.add_header("Authorization", "Bearer " + token)
    req.add_header("Accept", "application/vnd.github+json")
    req.add_header("User-Agent", "workbuddy-push")
    if data:
        req.add_header("Content-Type", "application/json")
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            return r.status, json.loads(r.read().decode("utf-8") or "{}")
    except urllib.error.HTTPError as e:
        return e.code, json.loads(e.read().decode("utf-8") or "{}")
    except urllib.error.URLError as e:
        raise SystemExit("[FAIL] 网络不可达: %s" % e)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--owner", default="zhangyanfei6688-hash")
    ap.add_argument("--repo", default="account-ops-workbench")
    ap.add_argument("--branch", default="main")
    ap.add_argument("--create", action="store_true", help="仓库不存在时自动创建（私有）")
    ap.add_argument("--private", action="store_true", default=True)
    args = ap.parse_args()

    token = (sys.stdin.readline().strip() if not sys.stdin.isatty() else "") or os.environ.get("GITHUB_TOKEN", "")
    if not token:
        raise SystemExit("[FAIL] 未提供 token：请 echo <token> | python push_github.py 或设置 GITHUB_TOKEN")

    status, _ = api("GET", "/repos/%s/%s" % (args.owner, args.repo), token)
    if status == 404:
        if not args.create:
            raise SystemExit("[FAIL] 仓库 %s/%s 不存在，加 --create 自动创建" % (args.owner, args.repo))
        status, info = api("POST", "/user/repos", token, {
            "name": args.repo,
            "description": "账号运营分析台：腾讯文档 → 资料库数据表 → 单文件 HTML 工作台",
            "private": True,
            "auto_init": False,
        })
        if status not in (200, 201):
            raise SystemExit("[FAIL] 创建仓库失败 %s: %s" % (status, info.get("message")))
        print("[OK] 已创建仓库 %s/%s（私有）" % (args.owner, args.repo))
    elif status != 200:
        raise SystemExit("[FAIL] 访问仓库失败 %s（token 权限不足或仓库名不对）" % status)
    else:
        print("[OK] 仓库已存在 %s/%s" % (args.owner, args.repo))

    sh(["git", "branch", "-M", args.branch])
    url = "https://%s@github.com/%s/%s.git" % (token, args.owner, args.repo)
    sh(["git", "remote", "remove", "origin"], check=False)
    sh(["git", "remote", "add", "origin", url])
    try:
        out = sh(["git", "push", "-u", "origin", args.branch], check=False)
    finally:
        # 无论成功失败，都把凭据从 remote 里抹掉
        sh(["git", "remote", "set-url", "origin", "https://github.com/%s/%s.git" % (args.owner, args.repo)], check=False)

    if "Everything up-to-date" in out or "->" in out or "branch" in out:
        print("[OK] 推送完成: https://github.com/%s/%s" % (args.owner, args.repo))
    else:
        print("[WARN] push 输出异常:\n" + out)

    # 校验：远程是否真的有提交
    st, commits = api("GET", "/repos/%s/%s/commits?per_page=5" % (args.owner, args.repo), token)
    if st == 200 and isinstance(commits, list):
        print("[VERIFY] 远程 commit 数(最近页)=%d" % len(commits))
        for c in commits:
            print("  - %s %s" % (c.get("sha", "")[:7], (c.get("commit") or {}).get("message", "").splitlines()[0]))
    else:
        print("[WARN] 校验失败 %s: %s" % (st, commits.get("message") if isinstance(commits, dict) else commits))


if __name__ == "__main__":
    main()

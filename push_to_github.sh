#!/usr/bin/env bash
# wechat-ai-briefing 发布到 GitHub 的一键脚本
# 用法：
#   1. 先到 https://github.com/new 网页创建空仓库：
#         Repository name: wechat-ai-briefing
#         Public, 不要勾 README / .gitignore / LICENSE（这里已经有了）
#   2. 然后在终端运行：
#         bash push_to_github.sh
#      推送时会要你输入 GitHub 用户名 + 个人访问令牌（PAT）作为密码
set -e

REPO="wechat-ai-briefing"
USER="jiangkaili"
URL="https://github.com/${USER}/${REPO}.git"

cd "$(dirname "$0")"

if ! git remote get-url origin >/dev/null 2>&1; then
    git remote add origin "$URL"
    echo "[+] remote origin -> $URL"
else
    git remote set-url origin "$URL"
    echo "[=] remote origin = $URL"
fi

echo "[*] pushing main → origin ..."
git push -u origin main

echo
echo "✓ Done. 仓库地址: https://github.com/${USER}/${REPO}"

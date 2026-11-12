#!/usr/bin/env bash
# 一键部署：导航页 + 万千知识库前端
# 用法：bash deploy.sh            （只部署导航页）
#       bash deploy.sh --with-kb  （连知识库前端一起）
set -e

KEY="$HOME/.ssh/wanqian_deploy"
HOST="root@42.193.158.63"
KB_FE="C:/Users/maxl/WorkBuddy/2026-09-18-16-52-56/knowledge-base/frontend"

cd "$(dirname "$0")"
TMP=".deploy-tmp"
rm -rf "$TMP"
mkdir -p "$TMP"

python build_nav.py
tar -czf "$TMP/nav.tgz" index.html

FILES="$TMP/nav.tgz"
CMD="mkdir -p /opt/nav && tar -xzf /tmp/nav.tgz -C /opt/nav"

if [ "$1" = "--with-kb" ]; then
  if [ ! -d "$KB_FE/dist" ]; then
    echo "缺 $KB_FE/dist，先在那边 npm run build"; exit 1
  fi
  tar -czf "$TMP/kb.tgz" -C "$KB_FE/dist" .
  FILES="$FILES $TMP/kb.tgz"
  # 先解到 dist.new 再整体切换，避免解压中途页面 404
  CMD="$CMD && rm -rf /opt/kb/dist.new && mkdir -p /opt/kb/dist.new && tar -xzf /tmp/kb.tgz -C /opt/kb/dist.new && rm -rf /opt/kb/dist.old && (mv /opt/kb/dist /opt/kb/dist.old 2>/dev/null || true) && mv /opt/kb/dist.new /opt/kb/dist"
fi

scp -i "$KEY" -o ConnectTimeout=15 $FILES "$HOST:/tmp/"
ssh -i "$KEY" -o ConnectTimeout=15 "$HOST" "$CMD && rm -f /tmp/nav.tgz /tmp/kb.tgz && echo DEPLOYED"

rm -rf "$TMP"
echo "--- 线上校验 ---"
curl -s -o /dev/null -w "导航页 %{http_code}\n" http://42.193.158.63/nav/
curl -s http://42.193.158.63/nav/ | grep -c appinstall | xargs -I{} echo "APP 卡片命中 {} 处"

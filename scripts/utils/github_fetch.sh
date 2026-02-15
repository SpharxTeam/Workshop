#!/bin/bash
# github_fetch.sh - 通过镜像加速从 GitHub 下载文件
# 用法: ./github_fetch.sh <github_raw_url> [output_filename]

set -e

# 镜像代理列表（按优先级排序）
MIRRORS=(
    "https://gh-proxy.com/"
    "https://ghproxy.net/"
    "https://gh.llkk.cc/"
    "https://gh.api.99988866.xyz/"
)

if [ $# -lt 1 ]; then
    echo "用法: $0 <github_raw_url> [output_filename]"
    exit 1
fi

URL="$1"
OUTPUT="${2:-$(basename "$URL")}"

for mirror in "${MIRRORS[@]}"; do
    PROXY_URL="${mirror}${URL}"
    echo "尝试使用镜像: $mirror"
    if wget --timeout=10 --tries=2 -q --show-progress "$PROXY_URL" -O "$OUTPUT"; then
        echo "下载成功: $OUTPUT"
        exit 0
    else
        echo "镜像 $mirror 失败，尝试下一个..."
    fi
done

echo "所有镜像均失败，请检查网络或稍后重试"
exit 1
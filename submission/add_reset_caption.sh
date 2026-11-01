#!/usr/bin/env bash
set -euo pipefail
out="$1"
font="${MICRODUCK_VIDEO_FONT:-/mnt/c/Windows/Fonts/meiryo.ttc}"
if [[ ! -f "$font" ]]; then
  printf '%s\n' '日本語フォントがありません。MICRODUCK_VIDEO_FONT にフォントのパスを設定してください。' >&2
  exit 1
fi
ffmpeg -v error -y -i "$out/comparison_reset.mp4" \
  -vf "drawtext=fontfile=$font:text=各8秒は独立した試行・毎回同じ初期状態にリセット:x=16:y=92:fontsize=21:fontcolor=white:box=1:boxcolor=black@0.8:boxborderw=5" \
  -c:v libx264 -crf 18 -pix_fmt yuv420p -an "$out/comparison_reset_labeled_jp.mp4"

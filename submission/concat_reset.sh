#!/usr/bin/env bash
set -euo pipefail
out="$1"
cd "$out"
list=$(mktemp)
trap 'rm -f "$list"' EXIT
for phase in FORWARD RIGHT LEFT BACKWARD; do
 for policy in Baseline Footslip_m1; do
  printf "file '%s/%s_%s.mp4'\n" "$PWD" "$policy" "$phase" >> "$list"
 done
done
ffmpeg -v error -y -f concat -safe 0 -i "$list" -c copy comparison_reset.mp4
ffprobe -v error -show_entries stream=nb_frames,r_frame_rate -show_entries format=duration -of default=nw=1 comparison_reset.mp4

#!/bin/bash
# WebM → MP4 변환 스크립트
# 사용법: ./convert_to_mp4.sh [입력파일.webm]
# 입력 없으면 Downloads 폴더의 최신 assembly-*.webm 파일을 자동 선택

INPUT="$1"
if [ -z "$INPUT" ]; then
  INPUT=$(ls -t ~/Downloads/assembly-*.webm 2>/dev/null | head -1)
fi

if [ -z "$INPUT" ] || [ ! -f "$INPUT" ]; then
  echo "WebM 파일을 찾을 수 없습니다."
  echo "사용법: ./convert_to_mp4.sh 파일명.webm"
  exit 1
fi

OUTPUT="${INPUT%.webm}.mp4"
echo "변환 중: $INPUT → $OUTPUT"
ffmpeg -i "$INPUT" -c:v libx264 -preset fast -crf 23 -pix_fmt yuv420p -y "$OUTPUT"
echo ""
echo "완료: $OUTPUT"

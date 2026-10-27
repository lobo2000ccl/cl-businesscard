#!/bin/bash
# PC(맥/리눅스)에서 앱을 테스트 실행하는 스크립트
# 사용법: bash run_desktop.sh

echo "=== CL Business Card 데스크톱 테스트 ==="

# 가상환경 생성 (선택)
if [ ! -d "venv" ]; then
    echo "가상환경 생성 중..."
    python3 -m venv venv
fi
source venv/bin/activate

echo "필요한 패키지 설치 중..."
pip install -q -r requirements-desktop.txt

echo "앱 실행!"
python main.py

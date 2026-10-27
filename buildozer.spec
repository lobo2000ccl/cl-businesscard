[app]

# 앱 이름 (홈화면에 표시)
title = CL Business Card

# 패키지 이름 (영문/숫자만)
package.name = clbusinesscard

# 패키지 도메인 (고유 식별자, 보통 역순 도메인)
package.domain = com.rim

# 소스 코드 위치
source.dir = .

# 포함할 파일 확장자
source.include_exts = py,png,jpg,jpeg,ttf,json,kv,vcf,csv

# 포함할 폴더 (폰트)
source.include_patterns = fonts/*,icon.png,presplash.png

# 앱 버전
version = 1.0

# 필요한 파이썬 패키지
# - kivy: UI 프레임워크
# - pillow: 이미지 처리
# - pyjnius: 안드로이드 네이티브 기능(전화/문자/카메라)
# - plyer: 카메라/파일선택 등 플랫폼 기능
# - android: 안드로이드 API
# 주의: pytesseract는 안드로이드에서 Tesseract 엔진 바이너리가 별도 필요합니다.
# 현재는 안정성을 위해 OCR 없이 수동입력 중심으로 동작하며,
# 사진은 그대로 저장됩니다. (OCR 고도화는 추후 tesseract4android 연동 예정)
requirements = python3,kivy==2.3.0,pillow,pyjnius,android,openpyxl,et_xmlfile

# 화면 방향 (세로 고정)
orientation = portrait

# 앱 아이콘
icon.filename = %(source.dir)s/icon.png

# 시작 화면 이미지
presplash.filename = %(source.dir)s/presplash.png

# 시작화면 배경색 (민트)
android.presplash_color = #007a6e

# ───────────────────────────────────────
# 안드로이드 설정
# ───────────────────────────────────────

# 필요한 권한
# - CAMERA: 명함 촬영
# - READ/WRITE_EXTERNAL_STORAGE: 갤러리 사진 읽기, 데이터 저장
# - INTERNET: (선택) 향후 기능용
android.permissions = CAMERA,READ_EXTERNAL_STORAGE,WRITE_EXTERNAL_STORAGE,INTERNET,READ_MEDIA_IMAGES

# 안드로이드 API 레벨
android.api = 33
android.minapi = 24
android.ndk = 25b

# 지원 아키텍처 (대부분 폰 호환)
android.archs = arm64-v8a, armeabi-v7a

# python-for-android 안정 버전 고정 (최신 pip/Python3.14 호환 문제 회피)
p4a.branch = v2024.01.21
p4a.fork = kivy

# AndroidX 사용 (ML Kit 필수)
android.enable_androidx = True

# ML Kit 한국어 텍스트 인식 (온디바이스 OCR, API 키 불필요)
android.gradle_dependencies = com.google.mlkit:text-recognition-korean:16.0.1

# 빌드 타입 (debug: 테스트용 서명, 바로 설치 가능)
# release로 바꾸려면 서명 키 필요
android.release_artifact = apk

# 화면 꺼짐 방지 안 함
android.wakelock = False

# 로그 레벨
log_level = 2

# ───────────────────────────────────────
[buildozer]

# 로그 상세도
log_level = 2

# 루트 실행 경고 (CI에서는 1)
warn_on_root = 1

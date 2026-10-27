# 📇 CL Business Card — 림 명함집

Python(Kivy)으로 만든 안드로이드 명함 관리 앱입니다.

## ✨ 기능
- 📇 **명함첩** — 이름순/회사순/등록순 정렬, 초성 그룹, 실시간 검색
- 📷 **스캔** — 카메라 촬영 또는 갤러리에서 명함 사진 → 자동 인식(OCR)
- ✏️ **직접입력** — 손으로 명함 정보 입력
- 📂 **가져오기** — vCard(.vcf), CSV 파일에서 연락처 일괄 가져오기
- 📞 **바로 연결** — 전화 걸기, 문자, 이메일(앱 선택), 카카오톡
- 💾 **자동 저장** — 앱을 꺼도 데이터 유지

---

## 🚀 .apk 만들기 (가장 쉬운 방법 — GitHub Actions)

PC에 복잡한 개발 도구를 설치할 필요 없이, **GitHub에 올리기만 하면 자동으로 .apk가 만들어집니다.**

### 1단계 — GitHub 계정 만들기 (이미 있으면 건너뛰기)
1. https://github.com 접속
2. 무료 회원가입

### 2단계 — 새 저장소(Repository) 만들기
1. GitHub 로그인 후 오른쪽 위 **＋ → New repository**
2. Repository name: `cl-businesscard` (아무거나)
3. **Public** 선택
4. **Create repository** 클릭

### 3단계 — 이 폴더의 파일 전부 업로드
1. 만든 저장소에서 **Add file → Upload files**
2. 이 `CL-BusinessCard-App` 폴더 안의 **모든 파일과 폴더**를 드래그앤드롭
   - `main.py`, `screens.py`, `buildozer.spec`, `icon.png`, `presplash.png`
   - `fonts/` 폴더 (한글 폰트)
   - `.github/` 폴더 (⚠️ 이게 자동빌드 핵심! 숨김폴더라 빠지기 쉬움)
3. 아래 **Commit changes** 클릭

> 💡 `.github` 폴더가 안 올라가면 자동빌드가 안 돼요. 폴더째 올렸는지 꼭 확인하세요.

### 4단계 — 자동 빌드 시작
1. 저장소 상단 **Actions** 탭 클릭
2. **Build Android APK** 워크플로우 클릭
3. 오른쪽 **Run workflow** 버튼 클릭 → 다시 **Run workflow**
4. ⏳ **20~40분 기다리기** (처음엔 오래 걸려요)

### 5단계 — .apk 다운로드
1. 빌드가 끝나면 (초록 ✅ 표시)
2. 완료된 빌드 클릭 → 맨 아래 **Artifacts** 섹션
3. **CL-BusinessCard-APK** 클릭 → .zip 다운로드
4. 압축 풀면 `.apk` 파일이 나와요!

### 6단계 — 폰에 설치
1. .apk 파일을 폰으로 옮기기 (카톡 나에게 보내기 등)
2. 파일 탭 → "설치"
3. "출처를 알 수 없는 앱" 경고가 뜨면 → **허용** (한 번만)
4. 설치 완료! 홈화면에 **CL** 아이콘 생김 🎉

---

## 💻 PC에서 먼저 테스트 (선택)

안드로이드로 빌드하기 전에 PC(맥/리눅스/윈도우)에서 미리 돌려볼 수 있어요.

```bash
cd CL-BusinessCard-App
pip install -r requirements-desktop.txt
python main.py
```

> OCR(사진 자동인식)까지 테스트하려면 Tesseract 설치 필요:
> - 맥: `brew install tesseract tesseract-lang`
> - 우분투: `sudo apt install tesseract-ocr tesseract-ocr-kor`
> - 윈도우: https://github.com/UB-Mannheim/tesseract/wiki

---

## 📁 파일 구성
```
CL-BusinessCard-App/
├── main.py              # 앱 본체 (데이터/로직/화면전환)
├── screens.py           # 화면 UI (명함첩/상세/입력/스캔/가져오기)
├── buildozer.spec       # 안드로이드 빌드 설정
├── icon.png             # 앱 아이콘
├── presplash.png        # 시작 화면
├── fonts/
│   ├── NanumGothic.ttf       # 한글 폰트 (일반)
│   └── NanumGothicBold.ttf   # 한글 폰트 (굵게)
├── .github/workflows/
│   └── build.yml        # 자동 빌드 설정 ⚠️필수
├── requirements-desktop.txt  # PC 테스트용
└── README.md            # 이 파일
```

---

## ⚠️ 명함 자동인식(OCR)에 대해

- 폰에 포함된 Tesseract OCR 엔진으로 **인터넷 없이** 명함을 읽습니다.
- 명함 배치가 다양해서 **100% 정확하진 않아요.** 인식 후 틀린 부분만 손으로 고치면 됩니다.
- 깨끗하게, 빛 반사 없이, 평평하게 찍으면 인식률이 올라갑니다.

---

## 📝 참고
- 데이터는 폰 내부에만 저장됩니다 (외부 전송 없음).
- 명함 삭제/수정은 상세 화면에서 가능합니다.

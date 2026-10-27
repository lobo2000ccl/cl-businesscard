# -*- coding: utf-8 -*-
"""
CL Business Card — 림 명함집
Kivy 기반 안드로이드 명함 관리 앱
"""
import os
import json
import re
from datetime import datetime

from kivy.app import App
from kivy.core.window import Window
from kivy.core.text import LabelBase
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.scrollview import ScrollView
from kivy.uix.gridlayout import GridLayout
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.textinput import TextInput
from kivy.uix.image import Image, AsyncImage
from kivy.uix.widget import Widget
from kivy.uix.popup import Popup
from kivy.uix.spinner import Spinner
from kivy.graphics import Color, RoundedRectangle, Rectangle
from kivy.clock import Clock
from kivy.utils import platform
from kivy.metrics import dp

# ────────────────────────────────────────────────
# 색상 팔레트 (민트 테마)
# ────────────────────────────────────────────────
M1 = (0.878, 0.969, 0.953, 1)   # #e0f7f3
M2 = (0.698, 0.925, 0.890, 1)   # #b2ece3
M3 = (0.243, 0.812, 0.722, 1)   # #3ecfb8
M4 = (0.051, 0.659, 0.588, 1)   # #0da896
M5 = (0.0, 0.478, 0.431, 1)     # #007a6e
WHITE = (1, 1, 1, 1)
BG = (0.929, 0.980, 0.973, 1)   # #edfaf8
TEXT = (0.102, 0.220, 0.196, 1) # #1a3832
SUB = (0.290, 0.478, 0.447, 1)  # #4a7a72
MUTE = (0.541, 0.710, 0.682, 1) # #8ab5ae
ERR = (0.878, 0.333, 0.333, 1)  # #e05555

# 한글 폰트 등록 (buildozer가 함께 패키징)
FONT = "NanumGothic"
try:
    LabelBase.register(name="NanumGothic",
                       fn_regular="fonts/NanumGothic.ttf",
                       fn_bold="fonts/NanumGothicBold.ttf")
except Exception:
    FONT = "Roboto"


# ────────────────────────────────────────────────
# 데이터 저장/로드
# ────────────────────────────────────────────────
def get_data_path():
    if platform == "android":
        from android.storage import app_storage_path
        base = app_storage_path()
    else:
        base = os.path.expanduser("~")
    d = os.path.join(base, "cl_businesscard")
    os.makedirs(d, exist_ok=True)
    return os.path.join(d, "cards.json")


def load_cards():
    path = get_data_path()
    if os.path.exists(path):
        try:
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return [
        {"id": 1, "name": "김민준", "company": "삼성전자", "department": "반도체사업부",
         "title": "수석연구원", "phone": "010-1234-5678", "email": "minjun.kim@samsung.com",
         "address": "수원시 영통구", "memo": "", "photo": "", "createdAt": "2024-01-15"},
        {"id": 2, "name": "이서연", "company": "현대자동차", "department": "기술연구소",
         "title": "책임연구원", "phone": "010-9876-5432", "email": "seoyeon.lee@hyundai.com",
         "address": "화성시", "memo": "친절하신 분", "photo": "", "createdAt": "2024-02-20"},
        {"id": 3, "name": "박성호", "company": "LG화학", "department": "배터리사업부",
         "title": "팀장", "phone": "010-5555-1234", "email": "sh.park@lgchem.com",
         "address": "서울 영등포구", "memo": "", "photo": "", "createdAt": "2024-03-10"},
    ]


def save_cards(cards):
    try:
        with open(get_data_path(), "w", encoding="utf-8") as f:
            json.dump(cards, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print("저장 실패:", e)


# ────────────────────────────────────────────────
# 명함 텍스트 파싱 (OCR 결과 → 필드)
# ────────────────────────────────────────────────
TITLE_WORDS = ['대표이사', '부대표이사', '부대표', '대표', '회장', '부회장', '사장', '부사장',
    '전무이사', '전무', '상무이사', '상무', '본부장', '센터장', '연구소장', '수석연구원',
    '책임연구원', '선임연구원', '주임연구원', '연구원', '솔루션개발팀장', '개발팀장', '영업팀장',
    '기획팀장', '마케팅팀장', '생산팀장', '품질팀장', '팀장', '실장', '부장', '차장', '과장',
    '대리', '주임', '사원', '수석', '책임', '선임', '이사', '소장', '원장', '매니저', '엔지니어',
    '컨설턴트', '연구위원', '기술사', '기사']

ORG_TAIL = ['개발팀', '영업팀', '기획팀', '마케팅팀', '생산팀', '품질팀', '지원팀', '관리팀',
    '구매팀', '인사팀', '총무팀', '재무팀', '회계팀', '설계팀', '기술팀', '전략팀', '사업부',
    '본부', '연구소', '연구원', '센터', '사업부문', '부문']


def parse_card_text(text):
    r = {"name": "", "company": "", "department": "", "title": "",
         "phone": "", "email": "", "address": "", "memo": ""}
    lines = [l.strip() for l in text.split("\n") if l.strip()]

    # 이메일 (E. 접두사 제거)
    m = re.search(r"[\w.\-]+@[\w.\-]+\.\w+", text)
    if m:
        r["email"] = re.sub(r"^[A-Za-z]\.", "", m.group(0))

    # 전화 (모바일 우선)
    mob = re.search(r"(?:M|Mobile|휴대|핸드폰|H\.P)[\s.:]*([+]?[0-9][0-9\-\s]{8,})", text, re.I)
    if mob:
        r["phone"] = re.sub(r"\s+", "-", mob.group(1).strip()).strip("-")
    else:
        allp = re.findall(r"01[016789][\-\s]?[0-9]{3,4}[\-\s]?[0-9]{4}", text)
        if allp:
            r["phone"] = re.sub(r"[\s]+", "-", allp[0])
        else:
            anyp = re.findall(r"[\+]?[0-9]{2,4}[\-\s][0-9]{3,4}[\-\s][0-9]{3,4}", text)
            if anyp:
                r["phone"] = re.sub(r"\s+", "-", anyp[-1])

    # 직책 (가장 구체적인 것 우선)
    found = [t for t in TITLE_WORDS if t in text]
    if found:
        r["title"] = max(found, key=len)

    # 부서
    for line in lines:
        c = line.strip()
        if 2 <= len(c) <= 14 and any(c.endswith(t) for t in ORG_TAIL) and "/" not in c:
            if c != r["title"]:
                r["department"] = c
                break
    if not r["department"]:
        dm = re.search(r"([가-힣]{2,}(?:개발팀|영업팀|기획팀|마케팅팀|생산팀|품질팀|사업부|지원팀|관리팀))", text)
        if dm:
            r["department"] = dm.group(1)

    # 회사
    cm = re.search(r"(?:\(주\)|㈜)\s*[가-힣A-Za-z0-9]+", text)
    if cm:
        r["company"] = cm.group(0).strip()
    else:
        cm2 = re.search(r"([가-힣A-Za-z0-9]+)\s*(?:주식회사|\(주\))", text)
        if cm2:
            r["company"] = cm2.group(1).strip()
        else:
            em = re.search(r"^[A-Z][A-Z0-9&\s]{3,}$", text, re.M)
            if em:
                r["company"] = em.group(0).strip()

    # 주소
    am = re.search(r"(?:\d{5}\s*)?(?:서울|부산|대구|인천|광주|대전|울산|세종|경기|강원|충청|충북|충남|전라|전북|전남|경상|경북|경남|제주)[^\n]*", text)
    if am:
        r["address"] = re.sub(r"^\d{5}\s*", "", am.group(0)).strip()

    # 이름 (직책/회사/부서/조직어 제외, 공백이름 처리)
    exclude_h = set()
    for e in [r["title"], r["company"], r["department"]]:
        if e:
            exclude_h.add(re.sub(r"[^가-힣]", "", e))
    org_kw = ["팀", "부", "실", "주식", "이사", "과장", "부장", "차장", "대표", "연구", "센터",
              "본부", "개발", "솔루션", "사장", "대리", "주임", "전무", "상무", "회장", "원장",
              "소장", "매니저", "전자", "화학", "자동차", "중공업", "건설", "은행", "보험",
              "증권", "통신", "물산", "산업"]
    for line in lines:
        c = line.strip()
        if "@" in c or re.search(r"\d{3}", c):
            continue
        name_part = c
        for t in sorted(TITLE_WORDS, key=len, reverse=True):
            name_part = name_part.replace(t, "")
        hangul = re.sub(r"[^가-힣]", "", name_part.strip())
        if 2 <= len(hangul) <= 4:
            if hangul not in exclude_h and not any(w in hangul for w in org_kw):
                r["name"] = hangul
                break
    if not r["name"]:
        en = re.search(r"[A-Z][a-z]+\s+[A-Z][a-z]+", text)
        if en:
            r["name"] = en.group(0)
    return r


def parse_vcard(text):
    cards = []
    for entry in re.split(r"BEGIN:VCARD", text, flags=re.I):
        if not entry.strip():
            continue
        def get(k):
            m = re.search(k + r"[^:]*:([^\r\n]*)", entry, re.I)
            return m.group(1).strip() if m else ""
        fn = get("FN")
        if not fn:
            continue
        cards.append({"name": fn, "company": get("ORG").replace(";", " ").strip(),
                      "department": "", "title": get("TITLE"), "phone": get("TEL"),
                      "email": get("EMAIL"), "address": "", "memo": "", "photo": ""})
    return cards


def parse_csv(text):
    lines = text.strip().split("\n")
    if len(lines) < 2:
        return []
    headers = [h.strip().lower() for h in lines[0].split(",")]
    cmap = {"이름": "name", "name": "name", "회사": "company", "company": "company",
            "부서": "department", "department": "department", "직책": "title", "title": "title",
            "전화": "phone", "phone": "phone", "이메일": "email", "email": "email",
            "주소": "address", "address": "address", "메모": "memo", "memo": "memo"}
    out = []
    for line in lines[1:]:
        vals = [v.strip().strip('"') for v in line.split(",")]
        c = {"name": "", "company": "", "department": "", "title": "",
             "phone": "", "email": "", "address": "", "memo": "", "photo": ""}
        for i, hd in enumerate(headers):
            if hd in cmap and i < len(vals):
                c[cmap[hd]] = vals[i]
        if c["name"]:
            out.append(c)
    return out


# ────────────────────────────────────────────────
# UI 헬퍼 위젯
# ────────────────────────────────────────────────
def avatar_color(name):
    palette = [(0.051, 0.659, 0.588, 1), (0.043, 0.549, 0.486, 1),
               (0.243, 0.812, 0.722, 1), (0.0, 0.478, 0.431, 1),
               (0.0, 0.690, 0.608, 1)]
    idx = (ord(name[0]) if name else 0) % len(palette)
    return palette[idx]


class RoundBox(BoxLayout):
    """둥근 모서리 배경 박스"""
    def __init__(self, bg_color=WHITE, radius=16, **kwargs):
        super().__init__(**kwargs)
        self.bg_color = bg_color
        self.radius = dp(radius)
        with self.canvas.before:
            self._c = Color(*bg_color)
            self._r = RoundedRectangle(radius=[self.radius])
        self.bind(pos=self._upd, size=self._upd)

    def _upd(self, *a):
        self._r.pos = self.pos
        self._r.size = self.size

    def set_color(self, c):
        self._c.rgba = c


class MintButton(Button):
    """민트 그라디언트 느낌 버튼"""
    def __init__(self, bg=M4, fg=WHITE, radius=12, **kwargs):
        super().__init__(**kwargs)
        self.background_normal = ""
        self.background_color = (0, 0, 0, 0)
        self.color = fg
        self.font_name = FONT
        self._bg = bg
        self._radius = dp(radius)
        with self.canvas.before:
            self._c = Color(*bg)
            self._r = RoundedRectangle(radius=[self._radius])
        self.bind(pos=self._upd, size=self._upd)

    def _upd(self, *a):
        self._r.pos = self.pos
        self._r.size = self.size


class Avatar(Widget):
    """원형 아바타 (이니셜 또는 사진)"""
    def __init__(self, name="", photo="", size_dp=46, **kwargs):
        super().__init__(**kwargs)
        self.size_hint = (None, None)
        self.size = (dp(size_dp), dp(size_dp))
        self._name = name
        self._photo = photo
        with self.canvas:
            self._col = Color(*avatar_color(name))
            self._circle = RoundedRectangle(radius=[dp(size_dp / 2)])
        self.bind(pos=self._upd, size=self._upd)
        if photo and os.path.exists(photo):
            self._img = Image(source=photo, allow_stretch=True, keep_ratio=False)
            self.add_widget(self._img)
            self._col.rgba = (0, 0, 0, 0)
        else:
            self._label = Label(text=(name[0] if name else "?"), font_name=FONT,
                                bold=True, font_size=dp(size_dp * 0.42), color=WHITE)
            self.add_widget(self._label)

    def _upd(self, *a):
        self._circle.pos = self.pos
        self._circle.size = self.size
        if hasattr(self, "_img"):
            self._img.pos = self.pos
            self._img.size = self.size
        if hasattr(self, "_label"):
            self._label.pos = self.pos
            self._label.size = self.size


def toast(msg):
    """간단한 토스트 메시지"""
    if platform == "android":
        try:
            from jnius import autoclass, cast
            PythonActivity = autoclass("org.kivy.android.PythonActivity")
            Toast = autoclass("android.widget.Toast")
            activity = PythonActivity.mActivity
            String = autoclass("java.lang.String")
            def show(dt):
                t = Toast.makeText(activity, cast("java.lang.CharSequence",
                                   String(msg)), Toast.LENGTH_SHORT)
                t.show()
            Clock.schedule_once(show, 0)
            return
        except Exception:
            pass
    # 데스크톱 fallback — 팝업
    p = Popup(title="", separator_height=0, size_hint=(0.7, None), height=dp(80),
              content=Label(text=msg, font_name=FONT, color=WHITE))
    p.open()
    Clock.schedule_once(lambda dt: p.dismiss(), 1.5)


# ────────────────────────────────────────────────
# 네이티브 기능 (전화/문자/이메일/카톡)
# ────────────────────────────────────────────────
def open_uri(uri):
    if platform == "android":
        try:
            from jnius import autoclass, cast
            Intent = autoclass("android.content.Intent")
            Uri = autoclass("android.net.Uri")
            PythonActivity = autoclass("org.kivy.android.PythonActivity")
            intent = Intent(Intent.ACTION_VIEW)
            intent.setData(Uri.parse(uri))
            current = PythonActivity.mActivity
            current.startActivity(intent)
        except Exception as e:
            toast("실행 실패: %s" % e)
    else:
        import webbrowser
        webbrowser.open(uri)


def make_call(phone):
    open_uri("tel:" + re.sub(r"[^0-9+]", "", phone))


def send_sms(phone):
    open_uri("sms:" + re.sub(r"[^0-9+]", "", phone))


def send_email(email, app="default"):
    urls = {
        "default": "mailto:" + email,
        "gmail": "https://mail.google.com/mail/?view=cm&fs=1&to=" + email,
        "naver": "https://mail.naver.com/",
        "kakao": "https://mail.kakao.com/",
        "outlook": "https://outlook.live.com/mail/0/deeplink/compose?to=" + email,
    }
    open_uri(urls.get(app, urls["default"]))


def open_kakao():
    open_uri("kakaolink://open")
    Clock.schedule_once(lambda dt: toast("카카오톡 앱에서 친구를 찾아보세요"), 1.2)


# ────────────────────────────────────────────────
# OCR 실행 (pytesseract — 안드로이드/데스크톱)
# ────────────────────────────────────────────────
def run_ocr(image_path):
    """이미지에서 텍스트 추출. 실패하거나 지원 안 되면 빈 문자열.

    - 데스크톱(PC): Tesseract 설치돼 있으면 자동 인식.
    - 안드로이드: Tesseract 엔진이 기본 포함되지 않으므로 건너뜀
      (사진은 저장되고, 사용자가 보고 직접 입력).
    """
    if platform == "android":
        # 안드로이드는 OCR 건너뛰고 수동입력 유도 (앱 안정성 우선)
        return ""
    try:
        import pytesseract
        from PIL import Image as PILImage
        img = PILImage.open(image_path)
        try:
            text = pytesseract.image_to_string(img, lang="kor+eng")
        except Exception:
            text = pytesseract.image_to_string(img, lang="eng")
        return text
    except Exception as e:
        print("OCR 실패:", e)
        return ""


# ────────────────────────────────────────────────
# 메인 앱
# ────────────────────────────────────────────────
class CLBusinessCardApp(App):
    def build(self):
        self.title = "CL Business Card"
        Window.clearcolor = BG
        self.cards = load_cards()
        self.view = "list"
        self.selected = None
        self.search = ""
        self.sort_by = "name"
        self.edit_form = None
        self.scan_result = None
        self.scan_photo = ""
        self.import_preview = None
        self._form_inputs = {}
        self._scan_inputs = {}

        self.root_layout = BoxLayout(orientation="vertical")
        self.header = BoxLayout(orientation="horizontal", size_hint_y=None, height=dp(52),
                                padding=[dp(12), dp(8)], spacing=dp(8))
        self.content = BoxLayout(orientation="vertical")
        self.nav = self._build_nav()

        self.root_layout.add_widget(self.header)
        self.root_layout.add_widget(self.content)
        self.root_layout.add_widget(self.nav)

        # 안드로이드 권한 요청
        if platform == "android":
            self._request_android_permissions()

        self.refresh()
        return self.root_layout

    def _request_android_permissions(self):
        try:
            from android.permissions import request_permissions, Permission
            request_permissions([Permission.CAMERA, Permission.READ_EXTERNAL_STORAGE,
                                 Permission.WRITE_EXTERNAL_STORAGE])
        except Exception as e:
            print("권한 요청 실패:", e)

    # ── 네비게이션 ──
    def _build_nav(self):
        nav = BoxLayout(orientation="horizontal", size_hint_y=None, height=dp(60))
        with nav.canvas.before:
            Color(*WHITE)
            self._nav_bg = Rectangle()
        nav.bind(pos=lambda *a: setattr(self._nav_bg, "pos", nav.pos),
                 size=lambda *a: setattr(self._nav_bg, "size", nav.size))
        self._nav_buttons = {}
        for vid, icon, label in [("list", "📇", "명함첩"), ("scan", "📷", "스캔"),
                                 ("add", "✏️", "직접입력"), ("import", "📂", "가져오기")]:
            b = Button(background_color=(0, 0, 0, 0), font_name=FONT, font_size=dp(10))
            b.text = "%s\n%s" % (icon, label)
            b.color = MUTE
            b.halign = "center"
            b.bind(on_release=lambda inst, v=vid: self.goto(v))
            self._nav_buttons[vid] = b
            nav.add_widget(b)
        return nav

    def _update_nav(self):
        for vid, b in self._nav_buttons.items():
            b.color = M4 if self.view == vid else MUTE
            b.bold = (self.view == vid)

    # ── 헤더 ──
    def _update_header(self):
        self.header.clear_widgets()
        if self.view == "list":
            self.header.height = 0
            return
        self.header.height = dp(52)
        titles = {"detail": "명함 상세", "add": "명함 수정" if (self.edit_form and self.edit_form.get("id")) else "명함 추가",
                  "scan": "📷 명함 스캔", "import": "📂 가져오기"}
        back = Button(text="‹", font_name=FONT, font_size=dp(26), color=M4,
                      background_color=(0, 0, 0, 0), size_hint_x=None, width=dp(40))
        back.bind(on_release=lambda *a: self.go_back())
        self.header.add_widget(back)
        self.header.add_widget(Label(text=titles.get(self.view, ""), font_name=FONT,
                                     font_size=dp(17), bold=True, color=TEXT, halign="left",
                                     valign="middle", text_size=(dp(250), dp(40))))

    def go_back(self):
        self.stop_camera_if_any()
        if self.view == "add" and self.edit_form and self.edit_form.get("id"):
            self.view = "detail"
        else:
            self.view = "list"
        self.edit_form = None
        self.refresh()

    # ── 화면 전환 ──
    def goto(self, view, card=None):
        self.stop_camera_if_any()
        self.view = view
        if view == "detail":
            self.selected = card
        elif view == "add":
            self.edit_form = dict(card) if card else None
        elif view == "scan":
            self.scan_result = None
            self.scan_photo = ""
            self.import_preview = None
        elif view == "import":
            self.import_preview = None
        self.refresh()

    def refresh(self):
        import screens
        self._update_header()
        self._update_nav()
        self.content.clear_widgets()
        builders = {"list": screens.build_list_screen, "detail": screens.build_detail_screen,
                    "add": screens.build_edit_screen, "scan": screens.build_scan_screen,
                    "import": screens.build_import_screen}
        self.content.add_widget(builders.get(self.view, screens.build_list_screen)(self))

    # ── 검색/필터 ──
    def set_search(self, val):
        self.search = val
        # 검색은 리스트 화면에서만 갱신
        if self.view == "list":
            self.refresh()

    def filtered_cards(self):
        s = self.search.lower()
        out = [c for c in self.cards if s in " ".join([
            c.get("name", ""), c.get("company", ""), c.get("department", ""),
            c.get("title", ""), c.get("phone", ""), c.get("email", "")]).lower()]
        out.sort(key=lambda c: c.get(self.sort_by, "") or "")
        return out

    # ── 저장/삭제 ──
    def save_from_form(self, card_id):
        form = {k: ti.text.strip() for k, ti in self._form_inputs.items()}
        if not form.get("name"):
            toast("이름을 입력해주세요")
            return
        if self.edit_form and self.edit_form.get("photo"):
            form["photo"] = self.edit_form["photo"]
        else:
            form["photo"] = ""
        if card_id:
            form["id"] = card_id
            form["createdAt"] = next((c.get("createdAt", "") for c in self.cards if c["id"] == card_id), "")
            self.cards = [form if c["id"] == card_id else c for c in self.cards]
            self.selected = form
            toast("명함이 수정되었습니다")
            self.view = "detail"
        else:
            form["id"] = int(datetime.now().timestamp() * 1000)
            form["createdAt"] = datetime.now().strftime("%Y-%m-%d")
            self.cards.append(form)
            toast("명함이 등록되었습니다")
            self.view = "list"
        save_cards(self.cards)
        self.edit_form = None
        self.refresh()

    def confirm_delete(self, card):
        content = BoxLayout(orientation="vertical", spacing=dp(10), padding=dp(16))
        content.add_widget(Label(text="정말 삭제할까요?", font_name=FONT, color=TEXT))
        btns = BoxLayout(orientation="horizontal", spacing=dp(10), size_hint_y=None, height=dp(48))
        popup = Popup(title="삭제 확인", title_font=FONT, size_hint=(0.8, None), height=dp(180))
        yes = MintButton(text="삭제", bg=ERR, radius=10)
        no = MintButton(text="취소", bg=M1, fg=SUB, radius=10)
        def do_del(*a):
            self.cards = [c for c in self.cards if c["id"] != card["id"]]
            save_cards(self.cards)
            self.view = "list"
            self.selected = None
            popup.dismiss()
            toast("삭제되었습니다")
            self.refresh()
        yes.bind(on_release=do_del)
        no.bind(on_release=lambda *a: popup.dismiss())
        btns.add_widget(yes)
        btns.add_widget(no)
        content.add_widget(btns)
        popup.content = content
        popup.open()

    # ── 사진 선택 ──
    def pick_photo_for(self, card, context):
        if card.get("photo"):
            card["photo"] = ""
            if context == "detail":
                self.cards = [card if c["id"] == card.get("id") else c for c in self.cards]
                save_cards(self.cards)
            self.refresh()
            return
        self._pick_image(lambda path: self._set_photo(card, path, context))

    def _set_photo(self, card, path, context):
        card["photo"] = path
        if context == "detail" and card.get("id"):
            self.cards = [card if c["id"] == card.get("id") else c for c in self.cards]
            self.selected = card
            save_cards(self.cards)
            toast("사진이 등록되었습니다")
        elif context == "edit":
            self.edit_form = card
        self.refresh()

    def _pick_image(self, callback):
        if platform == "android":
            self._android_pick_image(callback)
        else:
            self._desktop_file_chooser(callback, ["*.png", "*.jpg", "*.jpeg"])

    def _android_pick_image(self, callback):
        try:
            from plyer import filechooser
            filechooser.open_file(on_selection=lambda sel: callback(sel[0]) if sel else None,
                                  filters=["image/*"])
        except Exception as e:
            toast("갤러리 열기 실패: %s" % e)

    def _desktop_file_chooser(self, callback, filters):
        from kivy.uix.filechooser import FileChooserIconView
        popup = Popup(title="파일 선택", title_font=FONT, size_hint=(0.95, 0.9))
        box = BoxLayout(orientation="vertical")
        fc = FileChooserIconView(filters=filters, path=os.path.expanduser("~"))
        box.add_widget(fc)
        pick = MintButton(text="선택", bg=M4, radius=10, size_hint_y=None, height=dp(48))
        def do_pick(*a):
            if fc.selection:
                popup.dismiss()
                callback(fc.selection[0])
        pick.bind(on_release=do_pick)
        box.add_widget(pick)
        popup.content = box
        popup.open()

    # ── 카메라 / 스캔 ──
    def start_camera(self):
        if platform == "android":
            self._android_camera()
        else:
            toast("데스크톱에서는 갤러리를 이용해주세요")
            self.pick_from_gallery()

    def _android_camera(self):
        try:
            from plyer import camera
            path = os.path.join(os.path.dirname(get_data_path()),
                                "scan_%d.jpg" % int(datetime.now().timestamp()))
            camera.take_picture(filename=path,
                                on_complete=lambda p: self.on_photo_captured(p))
        except Exception as e:
            toast("카메라 실행 실패: %s" % e)

    def on_photo_captured(self, path):
        if path and os.path.exists(path):
            self.process_scan(path)

    def pick_from_gallery(self):
        self._pick_image(lambda path: self.process_scan(path))

    def process_scan(self, image_path):
        self.scan_photo = image_path
        toast("명함을 인식하는 중...")
        # OCR은 시간이 걸리므로 다음 프레임에
        Clock.schedule_once(lambda dt: self._do_ocr(image_path), 0.3)

    def _do_ocr(self, image_path):
        text = run_ocr(image_path)
        if text.strip():
            self.scan_result = parse_card_text(text)
            toast("인식 완료! 확인 후 등록하세요")
        else:
            self.scan_result = {"name": "", "company": "", "department": "", "title": "",
                                "phone": "", "email": "", "address": "", "memo": ""}
            toast("자동 인식이 어려워요. 직접 입력해주세요")
        self.refresh()

    def register_scanned(self):
        form = {k: ti.text.strip() for k, ti in self._scan_inputs.items()}
        if not form.get("name"):
            toast("이름을 입력해주세요")
            return
        form["id"] = int(datetime.now().timestamp() * 1000)
        form["createdAt"] = datetime.now().strftime("%Y-%m-%d")
        form["photo"] = self.scan_photo or ""
        self.cards.append(form)
        save_cards(self.cards)
        toast("명함이 등록되었습니다")
        self.scan_result = None
        self.scan_photo = ""
        self.view = "list"
        self.refresh()

    def reset_scan(self):
        self.scan_result = None
        self.scan_photo = ""
        self.refresh()

    def stop_camera_if_any(self):
        pass

    # ── 가져오기 ──
    def pick_import_file(self):
        if platform == "android":
            try:
                from plyer import filechooser
                filechooser.open_file(
                    on_selection=lambda sel: self._load_import(sel[0]) if sel else None)
            except Exception as e:
                toast("파일 열기 실패: %s" % e)
        else:
            self._desktop_file_chooser(self._load_import, ["*.vcf", "*.csv"])

    def _load_import(self, path):
        try:
            with open(path, "r", encoding="utf-8") as f:
                text = f.read()
            if path.lower().endswith(".vcf"):
                self.import_preview = parse_vcard(text)
            else:
                self.import_preview = parse_csv(text)
            if not self.import_preview:
                toast("가져올 명함이 없어요")
            self.refresh()
        except Exception as e:
            toast("파일 읽기 실패: %s" % e)

    def confirm_import(self):
        base = int(datetime.now().timestamp() * 1000)
        for i, c in enumerate(self.import_preview):
            c["id"] = base + i
            c["createdAt"] = datetime.now().strftime("%Y-%m-%d")
            c.setdefault("photo", "")
            self.cards.append(c)
        save_cards(self.cards)
        n = len(self.import_preview)
        self.import_preview = None
        self.view = "list"
        toast("%d개 명함을 가져왔습니다" % n)
        self.refresh()

    def cancel_import(self):
        self.import_preview = None
        self.refresh()


if __name__ == "__main__":
    CLBusinessCardApp().run()

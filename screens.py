# -*- coding: utf-8 -*-
"""
화면(뷰) 구성 — 명함첩 / 상세 / 입력 / 스캔 / 가져오기
"""
import os
from datetime import datetime

from kivy.uix.boxlayout import BoxLayout
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.scrollview import ScrollView
from kivy.uix.label import Label
from kivy.uix.image import Image
from kivy.uix.widget import Widget
from kivy.uix.textinput import TextInput
from kivy.uix.popup import Popup
from kivy.uix.filechooser import FileChooserListView
from kivy.graphics import Color, RoundedRectangle, Rectangle
from kivy.metrics import dp
from kivy.utils import platform
from kivy.clock import Clock

import main as M
from main import (M1, M2, M3, M4, M5, WHITE, BG, TEXT, SUB, MUTE, ERR, FONT,
                  RoundBox, MintButton, Avatar, toast, avatar_color,
                  make_call, send_sms, send_email, open_kakao,
                  parse_card_text, parse_vcard, parse_csv, save_cards)


def hline():
    w = Widget(size_hint_y=None, height=dp(1))
    with w.canvas:
        Color(*M1)
        r = Rectangle()
    w.bind(pos=lambda *a: setattr(r, "pos", w.pos),
           size=lambda *a: setattr(r, "size", w.size))
    return w


def field_label(text):
    return Label(text=text, font_name=FONT, font_size=dp(11), color=MUTE,
                 bold=True, size_hint_y=None, height=dp(18), halign="left",
                 valign="middle", text_size=(dp(300), dp(18)))


def make_input(hint="", text="", multiline=False):
    ti = TextInput(text=text, hint_text=hint, font_name=FONT, font_size=dp(15),
                   multiline=multiline, size_hint_y=None,
                   height=dp(70) if multiline else dp(44),
                   padding=[dp(12), dp(12)], background_color=WHITE,
                   foreground_color=TEXT, cursor_color=M4)
    return ti


# ════════════════════════════════════════════════
# 명함첩 (리스트)
# ════════════════════════════════════════════════
def build_list_screen(app):
    root = BoxLayout(orientation="vertical")

    # 배너
    banner = FloatLayout(size_hint_y=None, height=dp(150))
    with banner.canvas.before:
        Color(*M5)
        rect = Rectangle()
    banner.bind(pos=lambda *a: setattr(rect, "pos", banner.pos),
                size=lambda *a: setattr(rect, "size", banner.size))

    title_box = BoxLayout(orientation="horizontal", spacing=dp(14),
                          size_hint=(1, None), height=dp(56),
                          pos_hint={"x": 0, "top": 0.95}, padding=[dp(16), 0])
    icon = Image(source="icon.png", size_hint=(None, None),
                 size=(dp(52), dp(52))) if os.path.exists("icon.png") else Widget(size_hint=(None, None), size=(dp(52), dp(52)))
    title_box.add_widget(icon)
    tcol = BoxLayout(orientation="vertical")
    tcol.add_widget(Label(text="CL명함첩", font_name=FONT, font_size=dp(11),
                          color=(1, 1, 1, 0.7), bold=True, halign="left", valign="bottom",
                          text_size=(dp(250), dp(16)), size_hint_y=None, height=dp(16)))
    tcol.add_widget(Label(text="CL", font_name=FONT, font_size=dp(30),
                          color=WHITE, bold=True, halign="left", valign="middle",
                          text_size=(dp(250), dp(34)), size_hint_y=None, height=dp(34)))
    tcol.add_widget(Label(text="총 %d개의 명함" % len(app.cards), font_name=FONT,
                          font_size=dp(12), color=(1, 1, 1, 0.7), halign="left",
                          valign="top", text_size=(dp(250), dp(16)), size_hint_y=None, height=dp(16)))
    title_box.add_widget(tcol)
    banner.add_widget(title_box)

    # 검색창
    search_box = RoundBox(bg_color=WHITE, radius=14, orientation="horizontal",
                          size_hint=(0.9, None), height=dp(46), spacing=dp(8),
                          padding=[dp(14), 0], pos_hint={"center_x": 0.5, "y": 0.08})
    search_box.add_widget(Label(text="🔍", font_name=FONT, font_size=dp(16),
                                size_hint_x=None, width=dp(24), color=M4))
    search_input = TextInput(hint_text="이름, 회사, 부서 검색...", font_name=FONT,
                             font_size=dp(15), multiline=False, background_color=(0, 0, 0, 0),
                             foreground_color=TEXT, cursor_color=M4, padding=[0, dp(12)])
    search_input.bind(text=lambda inst, val: app.set_search(val))
    search_box.add_widget(search_input)
    # 정렬 버튼 (탭하면 순환) — Spinner 드롭다운 UI 버그 회피
    sort_labels = {"name": "이름순", "company": "회사순", "createdAt": "등록순"}
    sort_order = ["name", "company", "createdAt"]
    sort_btn = MintButton(text=sort_labels.get(app.sort_by, "이름순"), bg=M1, fg=M5,
                          radius=8, font_size=dp(12), size_hint_x=None, width=dp(70))
    def on_sort(*a):
        cur = sort_order.index(app.sort_by) if app.sort_by in sort_order else 0
        app.sort_by = sort_order[(cur + 1) % len(sort_order)]
        app.refresh()
    sort_btn.bind(on_release=on_sort)
    search_box.add_widget(sort_btn)
    banner.add_widget(search_box)
    root.add_widget(banner)

    # 목록
    scroll = ScrollView()
    lst = BoxLayout(orientation="vertical", size_hint_y=None, spacing=0)
    lst.bind(minimum_height=lst.setter("height"))

    filtered = app.filtered_cards()
    if not filtered:
        empty = BoxLayout(orientation="vertical", size_hint_y=None, height=dp(200),
                          padding=[0, dp(60)])
        empty.add_widget(Label(text="📇", font_size=dp(52), size_hint_y=None, height=dp(60)))
        empty.add_widget(Label(text="명함이 없어요", font_name=FONT, font_size=dp(16),
                               color=MUTE, bold=True, size_hint_y=None, height=dp(24)))
        lst.add_widget(empty)
    else:
        # 그룹핑
        groups = {}
        for c in filtered:
            key = (c["name"][:1] if app.sort_by == "name" else c.get("company", "#")[:1]) or "#"
            groups.setdefault(key, []).append(c)
        for key in sorted(groups.keys()):
            gh = Label(text=key, font_name=FONT, font_size=dp(12), color=M5, bold=True,
                       size_hint_y=None, height=dp(26), halign="left", valign="middle",
                       text_size=(dp(400), dp(26)), padding=[dp(16), 0])
            with gh.canvas.before:
                Color(*M1)
                gr = Rectangle()
            gh.bind(pos=lambda i, *a, r=gr: setattr(r, "pos", i.pos),
                    size=lambda i, *a, r=gr: setattr(r, "size", i.size))
            lst.add_widget(gh)
            for card in groups[key]:
                lst.add_widget(_card_row(app, card))

    scroll.add_widget(lst)
    root.add_widget(scroll)
    return root


def _card_row(app, card):
    row = BoxLayout(orientation="horizontal", size_hint_y=None, height=dp(70),
                    padding=[dp(16), dp(10)], spacing=dp(13))
    with row.canvas.before:
        Color(*WHITE)
        rb = Rectangle()
        Color(*M1)
        ln = Rectangle()
    def upd(*a):
        rb.pos = row.pos
        rb.size = row.size
        ln.pos = (row.x, row.y)
        ln.size = (row.width, dp(1))
    row.bind(pos=upd, size=upd)

    av = Avatar(name=card["name"], photo=card.get("photo", ""), size_dp=46)
    av_wrap = BoxLayout(size_hint_x=None, width=dp(46))
    av_wrap.add_widget(av)
    row.add_widget(av_wrap)

    info = BoxLayout(orientation="vertical")
    info.add_widget(Label(text=card["name"], font_name=FONT, font_size=dp(16), bold=True,
                          color=TEXT, halign="left", valign="middle",
                          text_size=(dp(240), dp(22)), size_hint_y=None, height=dp(22)))
    sub = " · ".join([x for x in [card.get("company"), card.get("department"),
                                  card.get("title")] if x])
    info.add_widget(Label(text=sub, font_name=FONT, font_size=dp(13), color=SUB,
                          halign="left", valign="middle", shorten=True,
                          text_size=(dp(240), dp(18)), size_hint_y=None, height=dp(18)))
    if card.get("phone"):
        info.add_widget(Label(text=card["phone"], font_name=FONT, font_size=dp(12),
                              color=MUTE, halign="left", valign="middle",
                              text_size=(dp(240), dp(16)), size_hint_y=None, height=dp(16)))
    row.add_widget(info)
    row.add_widget(Label(text="›", font_name=FONT, font_size=dp(22), color=M3,
                         size_hint_x=None, width=dp(20)))

    # 터치 시 상세 이동
    btn = M.Button(background_color=(0, 0, 0, 0), size_hint=(1, 1))
    btn.bind(on_release=lambda *a: app.goto("detail", card))
    overlay = FloatLayout(size_hint_y=None, height=dp(70))
    overlay.add_widget(row)
    overlay.add_widget(btn)
    return overlay


# ════════════════════════════════════════════════
# 상세 화면
# ════════════════════════════════════════════════
def build_detail_screen(app):
    card = app.selected
    root = BoxLayout(orientation="vertical")
    scroll = ScrollView()
    body = BoxLayout(orientation="vertical", size_hint_y=None, spacing=0)
    body.bind(minimum_height=body.setter("height"))

    # 헤더 (아바타)
    header = FloatLayout(size_hint_y=None, height=dp(200))
    with header.canvas.before:
        Color(*M5)
        hr = Rectangle()
    header.bind(pos=lambda *a: setattr(hr, "pos", header.pos),
                size=lambda *a: setattr(hr, "size", header.size))
    big_av = Avatar(name=card["name"], photo=card.get("photo", ""), size_dp=88)
    big_av.pos_hint = {"center_x": 0.5, "top": 0.92}
    header.add_widget(big_av)
    # 사진 등록 버튼
    photo_btn = MintButton(text="📷 사진 등록" if not card.get("photo") else "🗑 사진 삭제",
                           bg=(1, 1, 1, 0.2), fg=WHITE, radius=20,
                           font_size=dp(11), size_hint=(None, None),
                           size=(dp(120), dp(28)), pos_hint={"center_x": 0.5, "y": 0.28})
    photo_btn.bind(on_release=lambda *a: app.pick_photo_for(card, "detail"))
    header.add_widget(photo_btn)
    name_lbl = Label(text=card["name"], font_name=FONT, font_size=dp(22), bold=True,
                     color=WHITE, size_hint=(1, None), height=dp(30),
                     pos_hint={"center_x": 0.5, "y": 0.13})
    header.add_widget(name_lbl)
    sub_lbl = Label(text=" · ".join([x for x in [card.get("company"), card.get("title")] if x]),
                    font_name=FONT, font_size=dp(13), color=(1, 1, 1, 0.85),
                    size_hint=(1, None), height=dp(20), pos_hint={"center_x": 0.5, "y": 0.06})
    header.add_widget(sub_lbl)
    body.add_widget(header)

    # 액션 버튼 (전화/이메일/카톡/문자)
    actions = BoxLayout(orientation="horizontal", size_hint_y=None, height=dp(76),
                        spacing=dp(8), padding=[dp(16), dp(12)])
    act_data = []
    if card.get("phone"):
        act_data.append(("📞", "전화", M4, lambda: make_call(card["phone"])))
    if card.get("email"):
        act_data.append(("✉️", "이메일", (0.31, 0.68, 1, 1),
                         lambda: _email_popup(card["email"])))
    if card.get("phone"):
        act_data.append(("💬", "카톡", (0.976, 0.816, 0, 1), lambda: open_kakao()))
        act_data.append(("💌", "문자", (0.63, 0.55, 0.82, 1),
                         lambda: send_sms(card["phone"])))
    for icon, label, color, fn in act_data:
        b = MintButton(bg=color, radius=14)
        b.text = "%s\n%s" % (icon, label)
        b.font_name = FONT
        b.font_size = dp(11)
        b.halign = "center"
        b.bind(on_release=lambda inst, f=fn: f())
        actions.add_widget(b)
    body.add_widget(actions)

    # 정보 카드
    info_card = RoundBox(bg_color=WHITE, radius=18, orientation="vertical",
                         size_hint_y=None, padding=[dp(20), dp(10)], spacing=0)
    rows = [("🏢", "회사", card.get("company")), ("👥", "부서", card.get("department")),
            ("💼", "직책", card.get("title")), ("📞", "전화번호", card.get("phone")),
            ("✉️", "이메일", card.get("email")), ("📍", "주소", card.get("address")),
            ("📝", "메모", card.get("memo"))]
    h = dp(10)
    for icon, label, val in rows:
        if not val:
            continue
        r = BoxLayout(orientation="horizontal", size_hint_y=None, height=dp(48),
                      spacing=dp(12), padding=[0, dp(8)])
        r.add_widget(Label(text=icon, font_name=FONT, font_size=dp(17),
                           size_hint_x=None, width=dp(24)))
        tc = BoxLayout(orientation="vertical")
        tc.add_widget(Label(text=label, font_name=FONT, font_size=dp(11), color=MUTE,
                            bold=True, halign="left", valign="middle",
                            text_size=(dp(260), dp(16)), size_hint_y=None, height=dp(16)))
        tc.add_widget(Label(text=val, font_name=FONT, font_size=dp(15), color=TEXT,
                            halign="left", valign="middle",
                            text_size=(dp(260), dp(20)), size_hint_y=None, height=dp(20)))
        r.add_widget(tc)
        info_card.add_widget(r)
        h += dp(48)
    info_card.add_widget(Label(text="등록일: " + card.get("createdAt", ""), font_name=FONT,
                               font_size=dp(11), color=MUTE, halign="left", valign="middle",
                               text_size=(dp(300), dp(24)), size_hint_y=None, height=dp(24)))
    h += dp(24)
    info_card.height = h
    wrap = BoxLayout(size_hint_y=None, height=h + dp(12), padding=[dp(16), dp(6)])
    wrap.add_widget(info_card)
    body.add_widget(wrap)

    # 수정/삭제
    btns = BoxLayout(orientation="horizontal", size_hint_y=None, height=dp(56),
                     spacing=dp(10), padding=[dp(16), dp(6)])
    edit_b = MintButton(text="✏️ 수정", bg=M4, radius=12, font_size=dp(15), bold=True)
    edit_b.bind(on_release=lambda *a: app.goto("edit", card))
    del_b = MintButton(text="🗑 삭제", bg=WHITE, fg=ERR, radius=12, font_size=dp(15), bold=True)
    del_b.bind(on_release=lambda *a: app.confirm_delete(card))
    btns.add_widget(edit_b)
    btns.add_widget(del_b)
    body.add_widget(btns)
    body.add_widget(Widget(size_hint_y=None, height=dp(30)))

    scroll.add_widget(body)
    root.add_widget(scroll)
    return root


def _email_popup(email):
    content = BoxLayout(orientation="vertical", spacing=dp(2), padding=dp(10))
    content.add_widget(Label(text="받는 사람: " + email, font_name=FONT,
                             font_size=dp(12), color=MUTE, size_hint_y=None, height=dp(30)))
    apps = [("기본 메일", "default"), ("Gmail", "gmail"), ("네이버 메일", "naver"),
            ("카카오메일", "kakao"), ("Outlook", "outlook")]
    popup = Popup(title="이메일 앱 선택", title_font=FONT, size_hint=(0.85, None),
                  height=dp(360))
    for name, key in apps:
        b = MintButton(text=name, bg=M1, fg=TEXT, radius=10, size_hint_y=None,
                       height=dp(46), font_size=dp(15))
        b.bind(on_release=lambda inst, k=key: (send_email(email, k), popup.dismiss()))
        content.add_widget(b)
    popup.content = content
    popup.open()


# ════════════════════════════════════════════════
# 입력/수정 화면
# ════════════════════════════════════════════════
def build_edit_screen(app):
    form = dict(app.edit_form) if app.edit_form else {
        "name": "", "company": "", "department": "", "title": "",
        "phone": "", "email": "", "address": "", "memo": "", "photo": ""}
    app._form_inputs = {}
    root = ScrollView()
    body = BoxLayout(orientation="vertical", size_hint_y=None, spacing=dp(12),
                     padding=dp(16))
    body.bind(minimum_height=body.setter("height"))

    # 사진
    photo_card = RoundBox(bg_color=WHITE, radius=16, orientation="vertical",
                          size_hint_y=None, height=dp(200), padding=dp(16), spacing=dp(8))
    photo_card.add_widget(field_label("📸 명함 사진"))
    if form.get("photo") and os.path.exists(form["photo"]):
        photo_card.add_widget(Image(source=form["photo"], size_hint_y=None, height=dp(140)))
    else:
        ph_btn = MintButton(text="🖼️  명함 사진 등록 (선택)", bg=M1, fg=SUB, radius=12,
                            size_hint_y=None, height=dp(140), font_size=dp(14))
        ph_btn.bind(on_release=lambda *a: app.pick_photo_for(form, "edit"))
        photo_card.add_widget(ph_btn)
    body.add_widget(photo_card)

    # 필드
    form_card = RoundBox(bg_color=WHITE, radius=16, orientation="vertical",
                         size_hint_y=None, padding=dp(20), spacing=dp(8))
    fields = [("name", "이름 *", "👤"), ("company", "회사", "🏢"),
              ("department", "부서", "👥"), ("title", "직책", "💼"),
              ("phone", "전화번호", "📞"), ("email", "이메일", "✉️"),
              ("address", "주소", "📍"), ("memo", "메모", "📝")]
    fh = dp(40)
    for key, label, icon in fields:
        form_card.add_widget(field_label("%s %s" % (icon, label)))
        ti = make_input(hint=label, text=form.get(key, ""), multiline=(key == "memo"))
        app._form_inputs[key] = ti
        form_card.add_widget(ti)
        fh += dp(92) if key == "memo" else dp(66)
    form_card.height = fh
    body.add_widget(form_card)

    save_b = MintButton(text="💾 저장하기" if form.get("id") else "📇 명함 등록",
                        bg=M4, radius=14, size_hint_y=None, height=dp(52),
                        font_size=dp(16), bold=True)
    save_b.bind(on_release=lambda *a: app.save_from_form(form.get("id")))
    body.add_widget(save_b)
    body.add_widget(Widget(size_hint_y=None, height=dp(40)))
    root.add_widget(body)
    return root


# ════════════════════════════════════════════════
# 스캔 화면
# ════════════════════════════════════════════════
def build_scan_screen(app):
    root = BoxLayout(orientation="vertical", padding=dp(16), spacing=dp(12))

    if app.scan_result is not None:
        # 인식 결과 입력 폼
        scroll = ScrollView()
        body = BoxLayout(orientation="vertical", size_hint_y=None, spacing=dp(11))
        body.bind(minimum_height=body.setter("height"))
        if app.scan_photo and os.path.exists(app.scan_photo):
            body.add_widget(Image(source=app.scan_photo, size_hint_y=None, height=dp(180)))
        body.add_widget(Label(text="📋 정보 확인 후 등록하세요", font_name=FONT,
                              font_size=dp(15), bold=True, color=M4, size_hint_y=None,
                              height=dp(30), halign="left", valign="middle",
                              text_size=(dp(350), dp(30))))
        app._scan_inputs = {}
        labels = {"name": "이름", "company": "회사", "department": "부서",
                  "title": "직책", "phone": "전화", "email": "이메일",
                  "address": "주소", "memo": "메모"}
        for key, label in labels.items():
            body.add_widget(field_label(label))
            ti = make_input(hint=label, text=app.scan_result.get(key, ""))
            app._scan_inputs[key] = ti
            body.add_widget(ti)
        reg = MintButton(text="📇 명함 등록", bg=M4, radius=12, size_hint_y=None,
                         height=dp(48), font_size=dp(15), bold=True)
        reg.bind(on_release=lambda *a: app.register_scanned())
        body.add_widget(reg)
        retry = MintButton(text="다시 찍기", bg=M1, fg=SUB, radius=12, size_hint_y=None,
                           height=dp(44), font_size=dp(14))
        retry.bind(on_release=lambda *a: app.reset_scan())
        body.add_widget(retry)
        scroll.add_widget(body)
        root.add_widget(scroll)
        return root

    # 초기 선택 화면
    root.add_widget(Label(text="명함을 어떻게 등록할까요?", font_name=FONT, font_size=dp(13),
                          color=SUB, bold=True, size_hint_y=None, height=dp(24),
                          halign="left", valign="middle", text_size=(dp(350), dp(24))))
    cam_btn = MintButton(bg=M4, radius=16, size_hint_y=None, height=dp(90))
    cam_btn.text = "📷  카메라로 촬영\n실시간 카메라로 명함 찍기"
    cam_btn.font_name = FONT
    cam_btn.font_size = dp(15)
    cam_btn.halign = "center"
    cam_btn.bind(on_release=lambda *a: app.start_camera())
    root.add_widget(cam_btn)
    gal_btn = MintButton(bg=WHITE, fg=TEXT, radius=16, size_hint_y=None, height=dp(90))
    gal_btn.text = "🖼️  갤러리에서 선택\n저장된 명함 사진 불러오기"
    gal_btn.font_name = FONT
    gal_btn.font_size = dp(15)
    gal_btn.halign = "center"
    gal_btn.bind(on_release=lambda *a: app.pick_from_gallery())
    root.add_widget(gal_btn)

    tip = RoundBox(bg_color=M1, radius=12, size_hint_y=None, height=dp(70), padding=dp(14))
    tip.add_widget(Label(text="💡 사진을 등록하면 자동으로 인식을 시도하고,\n내용을 확인·수정 후 등록할 수 있어요!",
                         font_name=FONT, font_size=dp(12), color=SUB, halign="left",
                         valign="middle", text_size=(dp(330), dp(50))))
    root.add_widget(tip)
    root.add_widget(Widget())
    return root


# ════════════════════════════════════════════════
# 가져오기 화면
# ════════════════════════════════════════════════
def build_import_screen(app):
    root = BoxLayout(orientation="vertical", padding=dp(16), spacing=dp(12))
    if app.import_preview is not None:
        root.add_widget(Label(text="📋 %d개 명함 미리보기" % len(app.import_preview),
                              font_name=FONT, font_size=dp(15), bold=True, color=M5,
                              size_hint_y=None, height=dp(30), halign="left",
                              valign="middle", text_size=(dp(350), dp(30))))
        scroll = ScrollView()
        lst = BoxLayout(orientation="vertical", size_hint_y=None, spacing=dp(8))
        lst.bind(minimum_height=lst.setter("height"))
        for c in app.import_preview:
            item = RoundBox(bg_color=WHITE, radius=12, orientation="horizontal",
                            size_hint_y=None, height=dp(56), padding=[dp(16), dp(8)],
                            spacing=dp(12))
            aw = BoxLayout(size_hint_x=None, width=dp(38))
            aw.add_widget(Avatar(name=c["name"], size_dp=38))
            item.add_widget(aw)
            tc = BoxLayout(orientation="vertical")
            tc.add_widget(Label(text=c.get("name", "(이름없음)"), font_name=FONT,
                                font_size=dp(15), bold=True, color=TEXT, halign="left",
                                valign="middle", text_size=(dp(240), dp(22)),
                                size_hint_y=None, height=dp(22)))
            tc.add_widget(Label(text=" · ".join([x for x in [c.get("company"), c.get("title")] if x]),
                                font_name=FONT, font_size=dp(12), color=SUB, halign="left",
                                valign="middle", text_size=(dp(240), dp(18)),
                                size_hint_y=None, height=dp(18)))
            item.add_widget(tc)
            lst.add_widget(item)
        scroll.add_widget(lst)
        root.add_widget(scroll)
        bb = BoxLayout(orientation="horizontal", size_hint_y=None, height=dp(52), spacing=dp(10))
        ok = MintButton(text="✅ 전체 가져오기", bg=M4, radius=12, bold=True)
        ok.bind(on_release=lambda *a: app.confirm_import())
        cancel = MintButton(text="취소", bg=M1, fg=SUB, radius=12)
        cancel.bind(on_release=lambda *a: app.cancel_import())
        bb.add_widget(ok)
        bb.add_widget(cancel)
        root.add_widget(bb)
        return root

    drop = MintButton(bg=M1, fg=M5, radius=20, size_hint_y=None, height=dp(170))
    drop.text = ("📂\n파일 가져오기\n\n"
                 "✅ Excel (.xlsx) — 리멤버 등 명함앱 내보내기\n"
                 "✅ vCard (.vcf) — 스마트폰 연락처\n"
                 "✅ CSV (.csv) — 엑셀 내보내기")
    drop.font_name = FONT
    drop.font_size = dp(14)
    drop.halign = "center"
    drop.bind(on_release=lambda *a: app.pick_import_file())
    root.add_widget(drop)

    guide = RoundBox(bg_color=WHITE, radius=14, orientation="vertical",
                     size_hint_y=None, height=dp(130), padding=dp(16), spacing=dp(8))
    guide.add_widget(Label(text="💡 리멤버 앱 명함 가져오기", font_name=FONT, font_size=dp(14),
                           bold=True, color=TEXT, size_hint_y=None, height=dp(20),
                           halign="left", valign="middle", text_size=(dp(330), dp(20))))
    guide.add_widget(Label(text="리멤버 앱 → 내보내기 → 엑셀(.xlsx) 저장 후\n여기서 그 파일을 선택하면 명함이 한번에 등록돼요!",
                           font_name=FONT, font_size=dp(12), color=SUB, halign="left",
                           valign="top", text_size=(dp(330), dp(70))))
    root.add_widget(guide)
    root.add_widget(Widget())
    return root

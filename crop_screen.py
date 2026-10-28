# -*- coding: utf-8 -*-
"""
수동 크롭 화면 — 사진에서 명함 영역을 드래그로 선택해 잘라냄.
Kivy 위젯만 사용 (안정적, 플랫폼 무관).
"""
import os
from datetime import datetime
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.image import Image
from kivy.uix.widget import Widget
from kivy.graphics import Color, Line, Rectangle
from kivy.metrics import dp
from kivy.clock import Clock


class CropWidget(FloatLayout):
    """사진 + 드래그 선택 박스."""
    def __init__(self, image_path, **kwargs):
        super().__init__(**kwargs)
        self.image_path = image_path
        # 이미지 표시
        self.img = Image(source=image_path, allow_stretch=True, keep_ratio=True)
        self.add_widget(self.img)
        # 선택 박스 (기본: 중앙 70%)
        self.sel = None          # (x, y, w, h) in widget coords
        self._drag_start = None
        self._mode = None        # 'new' or 'move'
        with self.canvas.after:
            self._ov_color = Color(0.05, 0.66, 0.59, 1)
            self._line = Line(rectangle=(0, 0, 0, 0), width=dp(2))
        self.bind(size=self._init_sel, pos=self._init_sel)
        Clock.schedule_once(self._init_sel, 0.1)

    def _img_rect(self):
        """이미지가 실제로 그려지는 영역 (letterbox 고려)."""
        iw, ih = self.img.norm_image_size
        ix = self.img.center_x - iw / 2
        iy = self.img.center_y - ih / 2
        return ix, iy, iw, ih

    def _init_sel(self, *a):
        ix, iy, iw, ih = self._img_rect()
        if iw <= 0 or ih <= 0:
            return
        # 기본 선택: 이미지의 가로 85%, 세로 55% (명함 비율)
        w = iw * 0.85
        h = ih * 0.5
        x = ix + (iw - w) / 2
        y = iy + (ih - h) / 2
        self.sel = [x, y, w, h]
        self._redraw()

    def _redraw(self):
        if not self.sel:
            return
        x, y, w, h = self.sel
        self._line.rectangle = (x, y, w, h)

    def on_touch_down(self, touch):
        if not self.collide_point(*touch.pos) or not self.sel:
            return super().on_touch_down(touch)
        x, y, w, h = self.sel
        # 박스 안이면 이동, 밖이면 새로 그리기
        if x <= touch.x <= x + w and y <= touch.y <= y + h:
            self._mode = "move"
            self._drag_start = (touch.x, touch.y, x, y)
        else:
            self._mode = "new"
            self._drag_start = (touch.x, touch.y)
            self.sel = [touch.x, touch.y, 0, 0]
        return True

    def on_touch_move(self, touch):
        if not self._mode or not self._drag_start:
            return super().on_touch_move(touch)
        ix, iy, iw, ih = self._img_rect()
        if self._mode == "new":
            sx, sy = self._drag_start
            x = min(sx, touch.x)
            y = min(sy, touch.y)
            w = abs(touch.x - sx)
            h = abs(touch.y - sy)
            # 이미지 영역 안으로 제한
            x = max(ix, x); y = max(iy, y)
            w = min(w, ix + iw - x); h = min(h, iy + ih - y)
            self.sel = [x, y, w, h]
        elif self._mode == "move":
            sx, sy, ox, oy = self._drag_start
            nx = ox + (touch.x - sx)
            ny = oy + (touch.y - sy)
            w, hh = self.sel[2], self.sel[3]
            nx = max(ix, min(nx, ix + iw - w))
            ny = max(iy, min(ny, iy + ih - hh))
            self.sel = [nx, ny, w, hh]
        self._redraw()
        return True

    def on_touch_up(self, touch):
        self._mode = None
        self._drag_start = None
        return super().on_touch_up(touch)

    def get_cropped_path(self):
        """선택 영역을 실제 이미지 좌표로 변환해 크롭한 파일 경로 반환."""
        try:
            from PIL import Image as PILImage, ImageOps
            if not self.sel:
                return self.image_path
            ix, iy, iw, ih = self._img_rect()
            sx, sy, sw, sh = self.sel
            if sw < dp(20) or sh < dp(20):
                return self.image_path  # 너무 작으면 원본
            # 위젯 좌표 → 이미지 내 비율 (y는 뒤집힘: Kivy는 아래가 0)
            rel_x = (sx - ix) / iw
            rel_y = (sy - iy) / ih
            rel_w = sw / iw
            rel_h = sh / ih
            # PIL (좌상단 0) 기준으로 y 뒤집기
            pil = PILImage.open(self.image_path)
            pil = ImageOps.exif_transpose(pil)
            W, H = pil.size
            left = int(rel_x * W)
            top = int((1 - rel_y - rel_h) * H)
            right = int((rel_x + rel_w) * W)
            bottom = int((1 - rel_y) * H)
            left = max(0, min(left, W)); right = max(0, min(right, W))
            top = max(0, min(top, H)); bottom = max(0, min(bottom, H))
            if right - left < 10 or bottom - top < 10:
                return self.image_path
            cropped = pil.crop((left, top, right, bottom))
            if cropped.mode not in ("RGB", "L"):
                cropped = cropped.convert("RGB")
            # OCR 정확도를 위해 크롭 결과가 작으면 업스케일 (긴 변 1600px 이상 보장)
            cw, ch = cropped.size
            target = 1600
            if max(cw, ch) < target:
                ratio = target / float(max(cw, ch))
                cropped = cropped.resize((int(cw * ratio), int(ch * ratio)), PILImage.LANCZOS)
            out = self.image_path.rsplit(".", 1)[0] + "_crop.jpg"
            cropped.save(out, "JPEG", quality=95)
            return out if os.path.exists(out) else self.image_path
        except Exception as e:
            print("크롭 실패:", e)
            return self.image_path

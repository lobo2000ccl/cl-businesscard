# -*- coding: utf-8 -*-
"""
안드로이드 네이티브 카메라/갤러리/파일 선택 (plyer 대체)
- Intent + onActivityResult 패턴을 pyjnius로 직접 구현
- plyer보다 안정적
"""
import os
from datetime import datetime
from kivy.utils import platform
from kivy.clock import Clock

_callback = None
_capture_path = None
_bound = False


def _ensure_bound():
    """activity result 콜백을 한 번만 바인딩."""
    global _bound
    if _bound or platform != "android":
        return
    try:
        from android import activity
        activity.bind(on_activity_result=_on_activity_result)
        _bound = True
    except Exception as e:
        print("activity 바인딩 실패:", e)


def _deliver(path):
    """메인 스레드에서 콜백 호출."""
    global _callback
    cb = _callback
    _callback = None
    if cb:
        Clock.schedule_once(lambda dt: cb(path), 0)


def _on_activity_result(request_code, result_code, intent):
    try:
        from jnius import autoclass, cast
        Activity = autoclass("android.app.Activity")
        if result_code != Activity.RESULT_OK:
            _deliver(None)
            return

        if request_code == 1001:
            # 카메라 — 썸네일 Bitmap이 intent.getExtras()["data"]로 옴
            try:
                if intent is not None:
                    extras = intent.getExtras()
                    if extras is not None:
                        from jnius import autoclass
                        bmp = extras.get("data")
                        if bmp is not None:
                            path = _save_bitmap(bmp)
                            _deliver(path)
                            return
            except Exception as e:
                print("카메라 썸네일 처리 실패:", e)
            # fallback: 지정 경로 파일
            global _capture_path
            if _capture_path and os.path.exists(_capture_path):
                _deliver(_capture_path)
            else:
                _deliver(None)
        elif request_code in (1002, 1003):
            # 갤러리/파일 — intent.getData()의 Uri → 실제 파일로 복사
            if intent is None:
                _deliver(None)
                return
            uri = intent.getData()
            if uri is None:
                _deliver(None)
                return
            path = _copy_uri_to_cache(uri)
            _deliver(path)
    except Exception as e:
        print("activity result 처리 실패:", e)
        _deliver(None)


def _copy_uri_to_cache(uri):
    """content:// Uri를 앱 캐시의 실제 파일로 복사."""
    try:
        from jnius import autoclass, cast
        PythonActivity = autoclass("org.kivy.android.PythonActivity")
        activity = PythonActivity.mActivity
        resolver = activity.getContentResolver()
        stream = resolver.openInputStream(uri)
        # 파일명 결정
        cache_dir = activity.getCacheDir().getAbsolutePath()
        out_path = os.path.join(cache_dir, "picked_%d.jpg" % int(datetime.now().timestamp()))
        # InputStream → 파일
        BufferedInputStream = autoclass("java.io.BufferedInputStream")
        FileOutputStream = autoclass("java.io.FileOutputStream")
        bis = BufferedInputStream(stream)
        fos = FileOutputStream(out_path)
        buf = bytearray(8192)
        JavaArray = autoclass  # noqa
        # read loop via Java byte[]
        from jnius import JavaClass, MetaJavaClass  # noqa
        barr = _new_byte_array(8192)
        while True:
            n = bis.read(barr, 0, 8192)
            if n == -1:
                break
            fos.write(barr, 0, n)
        fos.flush()
        fos.close()
        bis.close()
        return out_path if os.path.exists(out_path) else None
    except Exception as e:
        print("Uri 복사 실패:", e)
        return None


def _new_byte_array(size):
    """Java byte[] 생성."""
    return bytearray(size)


def _save_bitmap(bmp):
    """Bitmap을 캐시의 JPEG 파일로 저장하고 경로 반환."""
    try:
        from jnius import autoclass
        PythonActivity = autoclass("org.kivy.android.PythonActivity")
        activity = PythonActivity.mActivity
        cache_dir = activity.getCacheDir().getAbsolutePath()
        out_path = os.path.join(cache_dir, "capture_%d.jpg" % int(datetime.now().timestamp()))
        FileOutputStream = autoclass("java.io.FileOutputStream")
        Bitmap = autoclass("android.graphics.Bitmap")
        CompressFormat = autoclass("android.graphics.Bitmap$CompressFormat")
        fos = FileOutputStream(out_path)
        bmp.compress(CompressFormat.JPEG, 95, fos)
        fos.flush()
        fos.close()
        return out_path if os.path.exists(out_path) else None
    except Exception as e:
        print("Bitmap 저장 실패:", e)
        return None


# ─────────────────────────────────────
# 공개 API
# ─────────────────────────────────────
def take_photo(callback):
    """카메라로 촬영. 완료 시 callback(path 또는 None)."""
    global _callback, _capture_path
    if platform != "android":
        callback(None)
        return
    try:
        _ensure_bound()
        from jnius import autoclass
        PythonActivity = autoclass("org.kivy.android.PythonActivity")
        Intent = autoclass("android.content.Intent")
        MediaStore = autoclass("android.provider.MediaStore")
        activity = PythonActivity.mActivity

        # EXTRA_OUTPUT 없이 호출 → 썸네일 Bitmap이 결과로 옴 (FileProvider 불필요, 크래시 없음)
        intent = Intent(MediaStore.ACTION_IMAGE_CAPTURE)
        _callback = callback
        activity.startActivityForResult(intent, 1001)
    except Exception as e:
        print("카메라 실행 실패:", e)
        _callback = None
        callback(None)


def pick_image(callback):
    """갤러리에서 이미지 선택. 완료 시 callback(path 또는 None)."""
    global _callback
    if platform != "android":
        callback(None)
        return
    try:
        _ensure_bound()
        from jnius import autoclass
        PythonActivity = autoclass("org.kivy.android.PythonActivity")
        Intent = autoclass("android.content.Intent")
        activity = PythonActivity.mActivity

        intent = Intent(Intent.ACTION_GET_CONTENT)
        intent.setType("image/*")
        intent.addCategory(Intent.CATEGORY_OPENABLE)

        _callback = callback
        activity.startActivityForResult(intent, 1002)
    except Exception as e:
        print("갤러리 실행 실패:", e)
        _callback = None
        callback(None)


def pick_file(callback):
    """파일(.vcf/.csv 등) 선택. 완료 시 callback(path 또는 None)."""
    global _callback
    if platform != "android":
        callback(None)
        return
    try:
        _ensure_bound()
        from jnius import autoclass
        PythonActivity = autoclass("org.kivy.android.PythonActivity")
        Intent = autoclass("android.content.Intent")
        activity = PythonActivity.mActivity

        intent = Intent(Intent.ACTION_GET_CONTENT)
        intent.setType("*/*")
        intent.addCategory(Intent.CATEGORY_OPENABLE)

        _callback = callback
        activity.startActivityForResult(intent, 1003)
    except Exception as e:
        print("파일 선택 실패:", e)
        _callback = None
        callback(None)

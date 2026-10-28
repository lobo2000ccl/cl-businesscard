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
_capture_uri = None
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
            # 카메라 — MediaStore URI에 고해상도 원본 저장됨
            global _capture_uri
            try:
                if _capture_uri is not None:
                    path = _copy_uri_to_cache(_capture_uri)
                    if path:
                        _deliver(path)
                        return
            except Exception as e:
                print("카메라 원본 처리 실패:", e)
            # fallback: 썸네일
            try:
                if intent is not None:
                    extras = intent.getExtras()
                    if extras is not None:
                        bmp = extras.get("data")
                        if bmp is not None:
                            _deliver(_save_bitmap(bmp))
                            return
            except Exception as e:
                print("썸네일 fallback 실패:", e)
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


def _get_display_name(activity, uri):
    """Uri에서 원본 파일명 가져오기 (확장자 보존용)."""
    try:
        from jnius import autoclass
        OpenableColumns = autoclass("android.provider.OpenableColumns")
        resolver = activity.getContentResolver()
        cursor = resolver.query(uri, None, None, None, None)
        if cursor is not None:
            try:
                idx = cursor.getColumnIndex(OpenableColumns.DISPLAY_NAME)
                if cursor.moveToFirst() and idx >= 0:
                    name = cursor.getString(idx)
                    cursor.close()
                    return name
            except Exception:
                pass
            try:
                cursor.close()
            except Exception:
                pass
    except Exception as e:
        print("파일명 조회 실패:", e)
    return None


def _copy_uri_to_cache(uri):
    """content:// Uri를 앱 캐시의 실제 파일로 복사 (확장자 보존)."""
    try:
        from jnius import autoclass
        PythonActivity = autoclass("org.kivy.android.PythonActivity")
        activity = PythonActivity.mActivity
        resolver = activity.getContentResolver()

        # 원본 파일명에서 확장자 추출
        display_name = _get_display_name(activity, uri)
        ext = ""
        if display_name and "." in display_name:
            ext = "." + display_name.rsplit(".", 1)[-1].lower()
        if not ext:
            # MIME 타입으로 추측
            mime = resolver.getType(uri) or ""
            if "sheet" in mime or "excel" in mime:
                ext = ".xlsx"
            elif "image" in mime:
                ext = ".jpg"
            elif "csv" in mime:
                ext = ".csv"
            elif "vcard" in mime or "vcf" in mime:
                ext = ".vcf"
            else:
                ext = ".bin"

        cache_dir = activity.getCacheDir().getAbsolutePath()
        out_path = os.path.join(cache_dir, "picked_%d%s" % (int(datetime.now().timestamp()), ext))

        # InputStream → 파일 (Java 바이트 배열로 안정적 복사)
        stream = resolver.openInputStream(uri)
        FileOutputStream = autoclass("java.io.FileOutputStream")
        fos = FileOutputStream(out_path)

        # Java byte[] 생성 (jnius)
        from jnius import JArray
        import jnius
        barr = JArray(jnius.jbyte)(8192)
        while True:
            n = stream.read(barr, 0, 8192)
            if n == -1:
                break
            fos.write(barr, 0, n)
        fos.flush()
        fos.close()
        stream.close()

        if os.path.exists(out_path) and os.path.getsize(out_path) > 0:
            print("파일 복사 성공:", out_path, os.path.getsize(out_path), "bytes")
            return out_path
        return None
    except Exception as e:
        print("Uri 복사 실패:", e)
        return None


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
    """카메라로 촬영 (고해상도). MediaStore URI에 원본 저장 → FileProvider 불필요."""
    global _callback, _capture_uri
    _capture_uri = None
    if platform != "android":
        callback(None)
        return
    try:
        _ensure_bound()
        from jnius import autoclass, cast
        PythonActivity = autoclass("org.kivy.android.PythonActivity")
        Intent = autoclass("android.content.Intent")
        MediaStore = autoclass("android.provider.MediaStore")
        ContentValues = autoclass("android.content.ContentValues")
        activity = PythonActivity.mActivity

        # MediaStore에 이미지 엔트리 생성 → 그 URI를 EXTRA_OUTPUT으로 (고해상도 원본 저장)
        values = ContentValues()
        MediaColumns = autoclass("android.provider.MediaStore$MediaColumns")
        values.put(MediaColumns.DISPLAY_NAME, "cl_card_%d.jpg" % int(datetime.now().timestamp()))
        values.put(MediaColumns.MIME_TYPE, "image/jpeg")
        Images = autoclass("android.provider.MediaStore$Images$Media")
        resolver = activity.getContentResolver()
        _capture_uri = resolver.insert(Images.EXTERNAL_CONTENT_URI, values)

        intent = Intent(MediaStore.ACTION_IMAGE_CAPTURE)
        if _capture_uri is not None:
            intent.putExtra(MediaStore.EXTRA_OUTPUT, cast("android.os.Parcelable", _capture_uri))
            intent.addFlags(Intent.FLAG_GRANT_WRITE_URI_PERMISSION)
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

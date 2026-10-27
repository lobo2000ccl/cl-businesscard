# -*- coding: utf-8 -*-
"""
Google ML Kit 기반 명함 OCR (안드로이드 전용)
- pyjnius로 ML Kit Text Recognition (한국어) 호출
- 온디바이스, 인터넷 불필요, API 키 불필요
- 모든 단계를 방어적으로 처리하여 실패해도 앱이 죽지 않음
"""
from kivy.utils import platform
from kivy.clock import Clock


def _safe_cb(callback, text):
    """콜백을 메인 스레드에서 안전하게 호출."""
    try:
        Clock.schedule_once(lambda dt: callback(text or ""), 0)
    except Exception:
        try:
            callback(text or "")
        except Exception:
            pass


def mlkit_ocr(image_path, callback):
    """ML Kit으로 이미지에서 텍스트 추출. 실패 시 callback("")."""
    if platform != "android":
        _safe_cb(callback, "")
        return

    try:
        from jnius import autoclass, PythonJavaClass, java_method
        from android.runnable import run_on_ui_thread
    except Exception as e:
        print("[OCR] jnius 임포트 실패:", e)
        _safe_cb(callback, "")
        return

    # 결과 리스너 (Java 인터페이스 구현)
    try:
        class _OnSuccess(PythonJavaClass):
            __javainterfaces__ = ["com/google/android/gms/tasks/OnSuccessListener"]
            __javacontext__ = "app"

            def __init__(self, cb):
                super().__init__()
                self.cb = cb

            @java_method("(Ljava/lang/Object;)V")
            def onSuccess(self, result):
                try:
                    text = result.getText()
                    print("[OCR] 성공, 길이:", len(text or ""))
                    _safe_cb(self.cb, text or "")
                except Exception as ex:
                    print("[OCR] onSuccess 오류:", ex)
                    _safe_cb(self.cb, "")

        class _OnFailure(PythonJavaClass):
            __javainterfaces__ = ["com/google/android/gms/tasks/OnFailureListener"]
            __javacontext__ = "app"

            def __init__(self, cb):
                super().__init__()
                self.cb = cb

            @java_method("(Ljava/lang/Exception;)V")
            def onFailure(self, e):
                try:
                    print("[OCR] 실패:", e.getMessage() if e else "?")
                except Exception:
                    pass
                _safe_cb(self.cb, "")
    except Exception as e:
        print("[OCR] 리스너 정의 실패:", e)
        _safe_cb(callback, "")
        return

    @run_on_ui_thread
    def _run():
        try:
            InputImage = autoclass("com.google.mlkit.vision.common.InputImage")
            TextRecognition = autoclass("com.google.mlkit.vision.text.TextRecognition")
            KoreanBuilder = autoclass(
                "com.google.mlkit.vision.text.korean.KoreanTextRecognizerOptions$Builder")
            BitmapFactory = autoclass("android.graphics.BitmapFactory")

            bitmap = BitmapFactory.decodeFile(image_path)
            if bitmap is None:
                print("[OCR] 비트맵 디코드 실패:", image_path)
                _safe_cb(callback, "")
                return

            image = InputImage.fromBitmap(bitmap, 0)
            options = KoreanBuilder().build()
            recognizer = TextRecognition.getClient(options)
            task = recognizer.process(image)
            task.addOnSuccessListener(_OnSuccess(callback))
            task.addOnFailureListener(_OnFailure(callback))
        except Exception as ex:
            print("[OCR] ML Kit 실행 오류:", ex)
            _safe_cb(callback, "")

    try:
        _run()
    except Exception as e:
        print("[OCR] run_on_ui_thread 오류:", e)
        _safe_cb(callback, "")

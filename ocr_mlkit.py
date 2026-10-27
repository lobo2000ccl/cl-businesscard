# -*- coding: utf-8 -*-
"""
Google ML Kit 기반 명함 OCR (안드로이드 전용)
- pyjnius로 ML Kit Text Recognition (한국어) 호출
- 온디바이스, 인터넷 불필요, API 키 불필요
"""
from kivy.utils import platform


def mlkit_ocr(image_path, callback):
    """ML Kit으로 이미지에서 텍스트 추출.

    비동기(ML Kit은 콜백 기반)이므로 결과를 callback(text)로 전달.
    실패 시 callback("")를 호출.
    """
    if platform != "android":
        callback("")
        return

    try:
        from jnius import autoclass, PythonJavaClass, java_method
        from android.runnable import run_on_ui_thread

        # ML Kit 클래스들
        InputImage = autoclass("com.google.mlkit.vision.common.InputImage")
        TextRecognition = autoclass("com.google.mlkit.vision.text.TextRecognition")
        KoreanOptions = autoclass(
            "com.google.mlkit.vision.text.korean.KoreanTextRecognizerOptions$Builder")
        BitmapFactory = autoclass("android.graphics.BitmapFactory")

        # 결과 콜백 래퍼 (Java OnSuccessListener 구현)
        class SuccessListener(PythonJavaClass):
            __javainterfaces__ = ["com/google/android/gms/tasks/OnSuccessListener"]
            __javacontext__ = "app"

            def __init__(self, cb):
                super().__init__()
                self.cb = cb

            @java_method("(Ljava/lang/Object;)V")
            def onSuccess(self, result):
                try:
                    # result = Text 객체, getText()로 전체 텍스트
                    Text = autoclass("com.google.mlkit.vision.text.Text")
                    text = result.getText()
                    self.cb(text or "")
                except Exception as e:
                    print("ML Kit onSuccess 처리 실패:", e)
                    self.cb("")

        class FailureListener(PythonJavaClass):
            __javainterfaces__ = ["com/google/android/gms/tasks/OnFailureListener"]
            __javacontext__ = "app"

            def __init__(self, cb):
                super().__init__()
                self.cb = cb

            @java_method("(Ljava/lang/Exception;)V")
            def onFailure(self, e):
                print("ML Kit 인식 실패:", e.getMessage() if e else "unknown")
                self.cb("")

        @run_on_ui_thread
        def _recognize():
            try:
                bitmap = BitmapFactory.decodeFile(image_path)
                if bitmap is None:
                    callback("")
                    return
                image = InputImage.fromBitmap(bitmap, 0)
                options = KoreanOptions().build()
                recognizer = TextRecognition.getClient(options)
                task = recognizer.process(image)
                task.addOnSuccessListener(SuccessListener(callback))
                task.addOnFailureListener(FailureListener(callback))
            except Exception as e:
                print("ML Kit 처리 중 오류:", e)
                callback("")

        _recognize()

    except Exception as e:
        print("ML Kit 초기화 실패:", e)
        callback("")

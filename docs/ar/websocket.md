# بيانات السوق عبر WebSocket

[English](../websocket.md) | [日本語](../ja/websocket.md) | [繁體中文](../zh-TW/websocket.md) | [한국어](../ko/websocket.md) | [العربية](../ar/websocket.md)

تتطلب ميزة WebSocket تثبيت `python -m pip install ".[websocket]"`. احصل على ticket ثم اتصل عبر WSS واشترك في رموز التداول. يستخدم تنسيق wire غلاف Finger_desk الأساسي بترميز UTF-8 JSON داخل binary frame. اشتراك الأسعار يستخدم `action=3` و`msgType=1` و`content.tickerList`. يصدر ticket من `/ws-api/v1/auth/build-ticket` ويمرر إلى `/ws?ticket=...`؛ ولا يرسل handshake ترويسة `Origin`.

هذه واجهة متزامنة، لذا استدع `recv()` بانتظام. تعالج keepalive، وعند الانقطاع تنفذ إعادة اتصال أسية محدودة ثم تحصل على ticket جديد وتعاد اشتراكات الرموز الحالية. يعيد `unsubscribe()` إرسال مجموعة الرموز المتبقية، والقائمة الفارغة تمسح الاشتراك. القيمة الافتراضية لـ `max_reconnect_attempts` هي 3. لا يتضمن DTO المؤكد معرّف السوق ولا يدعم protobuf أو أحداث الحساب/الأوامر.

# أمثلة

[English](README.md) | [日本語](README.md) | [繁體中文](README.md) | [한국어](README.ko.md) | [العربية](README.ar.md)

شغّل النصوص من جذر المستودع بعد تثبيت SDK (`python -m pip install .`). للأمثلة الموثقة للقراءة فقط، عيّن `FINGER_TRADER_ACCESS_TOKEN` في shell أو مدير الأسرار. لا تضع قيمة حقيقية في المصدر أو سجل shell.

| النص | ما يوضحه | يغيّر حالة التداول؟ |
|---|---|---|
| `api_read_only.py` | قراءة السوق والحساب والمراكز وسجل الأوامر | لا |
| `authentication_example.py` | تسجيل OAuth باستخدام متغيرات البيئة | لا |
| `market_data_example.py` | الأسواق وفئات المنتجات | لا |
| `historical_bars_example.py` | استعلام OHLCV وتحويل Decimal اختياري | لا |
| `accounts_example.py` | ملف الجلسة والمحفظة | لا |
| `positions_example.py` | المراكز الحالية | لا |
| `order_history_example.py` | استعلام سجل الأوامر | لا |
| `websocket_example.py` | اشتراك الأسعار بتذكرة؛ يتطلب `.[websocket]` | لا |
| `dual_ma_strategy.py` | مثال محلي على شموع اصطناعية بلا API | لا |

تستخدم الأمثلة context manager لتحرير موارد الشبكة وتعالج أخطاء API/الشبكة المتوقعة، ولا تطبع رموز المصادقة. لا يوجد مثال لإرسال أمر لأن SDK لا ينفذ عمليات الكتابة لواجهة التطبيق الحالية. راجع [دليل الأوامر](../docs/orders.md).

```sh
python examples/market_data_example.py
```

يستخدم `dual_ma_strategy.py` واجهة الإشارات المحلية المستقلة. راجع [Hosted Strategy](../docs/hosted-strategies.md) لاستراتيجيات Desktop؛ Host الحالي من P1 لا ينفذ الأوامر.

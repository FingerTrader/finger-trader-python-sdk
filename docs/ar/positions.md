# المراكز

[English](../positions.md) | [日本語](../ja/positions.md) | [繁體中文](../zh-TW/positions.md) | [한국어](../ko/positions.md) | [العربية](../ar/positions.md)

يستدعي `client.positions.list()` المسار الحالي `POST /app-api/v1/order/get-holding-orders` ويرسل `{page, pageSize, query}`. يرتبط `order_status` بـ `orderType` (سوق `0`، محدد `1`)، وترتبط العملة بـ `coinType` (USD `0`، USDT `100`). يحدد الحساب عبر الجلسة الموثقة.

لا يدعم `account_id` اعتباطياً، ويؤدي تقديمه إلى `ValueError`. يمكن تصفية `market_type` باستخدام enum الخاص بالخادم. تعاد التكلفة والربح/الخسارة والهامش وفق نموذج استجابة الخادم الأصلي.

راجع [النص الإنجليزي](../positions.md) للأمثلة والمواصفات الكاملة.

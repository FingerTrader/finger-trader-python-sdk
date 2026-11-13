# الأوامر

[English](../orders.md) | [日本語](../ja/orders.md) | [繁體中文](../zh-TW/orders.md) | [한국어](../ko/orders.md) | [العربية](../ar/orders.md)

يدعم SDK حالياً قراءة سجل الأوامر فقط من App API الحالية. تقرأ `client.orders.history(*, page=1, limit=20, filters=None)` سجل الجلسة الموثقة، ويرتبط `limit` بـ `pageSize`. تشمل المرشحات wallet_type وmarket_type وorder_type وcoin_type وorder_side وstart_time وend_time.

توجد في API الحالية نقاط إنشاء وتعديل TP/SL وإلغاء وإغلاق، لكن SDK لم يربطها بعد. تستهدف الأساليب القديمة `submit` و`update_limit` و`cancel_limit` و`set_take_profit_loss` مسارات `api/mob` المتقاعدة؛ لا تستخدمها. لا تتضمن الوثائق مثال إرسال/إلغاء أمر. كما يعيد Host الحالي من P1 الرمز `UNSUPPORTED_CAPABILITY` لطلبات تداول Context المستضاف.

راجع [النص الإنجليزي](../orders.md) لمعلمات الطلب الدقيقة وأمثلة الشيفرة.

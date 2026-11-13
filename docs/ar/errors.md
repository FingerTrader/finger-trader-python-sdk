# الاستثناءات والأخطاء

[English](../errors.md) | [日本語](../ja/errors.md) | [繁體中文](../zh-TW/errors.md) | [한국어](../ko/errors.md) | [العربية](../ar/errors.md)

يشير `APIError` إلى فشل الخادم و`NetworkError` إلى فشل النقل. يعني `UnknownOutcomeError` أن طلب تغيير الحالة ربما وصل إلى الخادم؛ طابق الحالة قبل إعادة المحاولة. تؤدي الوسائط غير الصالحة إلى `ValueError` والعمليات غير المدعومة إلى `NotImplementedError`. تستخدم أخطاء Hosted قيمة `code` ثابتة.

للتفاصيل الكاملة للأساليب وحقول payload والقيود والأمثلة، راجع [المرجع التقني الإنجليزي](../errors.md).

# استكشاف الأخطاء وإصلاحها

[English](../troubleshooting.md) | [日本語](../ja/troubleshooting.md) | [繁體中文](../zh-TW/troubleshooting.md) | [한국어](../ko/troubleshooting.md) | [العربية](../ar/troubleshooting.md)

عند 401/403 تحقق من عناوين auth/app ونوع الرمز وانتهائه وصلاحيات الجلسة. يتطلب تسجيل الدخول بكلمة مرور قيمة OAuth Basic من مشغل الخدمة. مرر حقول CAPTCHA إذا طلبها التدفق. عند خطأ TLS تحقق من عنوان HTTPS وشهادة CA الموثوقة، ولا تعطل التحقق من الشهادات.

إذا كانت نتائج السوق/التاريخ فارغة فتحقق من ticker وmarket وinterval ووقت البدء والصلاحية. إذا اتصل WebSocket دون وصول أسعار فتحقق من ticket واسم ticker الدقيق والصلاحية وجلسة السوق واستدع `recv()` بانتظام. بعد `UnknownOutcomeError` طابق سجل الأوامر ولا تعاود الإرسال فوراً. لا يعمل Hosted Context إلا على thread المالك للـ callback النشط.

راجع [النص الإنجليزي](../troubleshooting.md) لمعلمات الطلب الدقيقة وأمثلة الشيفرة.

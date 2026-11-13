# اختبارات تكامل API الحية

[English](../integration-testing.md) | [日本語](../ja/integration-testing.md) | [繁體中文](../zh-TW/integration-testing.md) | [한국어](../ko/integration-testing.md) | [العربية](../ar/integration-testing.md)

تفصل مجموعة الاختبارات الاختيارية في `integration_tests/` عن اختبارات الوحدة المعتمدة على mock في `tests/`. تدعم أهداف `sandbox` و`dev` و`production-read-only`. يجب أن تستخدم جميع النقاط HTTPS (وWSS للمقابس) مع إبقاء تحقق TLS مفعلاً.

اضبط العناوين وبيانات الاعتماد التي يزودك بها مشغل الخدمة في `.env.integration`. يتطلب production تحديد `FINGER_TRADER_IT_ENABLED=1` والهدف `production-read-only` وقيمة التأكيد `YES`. عند عدم التفعيل لا ترسل الاختبارات طلبات شبكة؛ والإعداد الناقص يفشل قبل الطلب. الاختبار الإنتاجي للقراءة فقط ولا يرسل أوامر ولا يغير الأموال.

راجع [النص الإنجليزي](../integration-testing.md) لمعلمات الطلب الدقيقة وأمثلة الشيفرة.

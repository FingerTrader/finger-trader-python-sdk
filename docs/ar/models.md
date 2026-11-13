# النماذج وبيانات الاستجابة

[English](../models.md) | [日本語](../ja/models.md) | [繁體中文](../zh-TW/models.md) | [한국어](../ko/models.md) | [العربية](../ar/models.md)

تعيد أساليب HTTP كائن `ApiResponse`: يحتوي `.data` على payload الناجح، ويعكس `.code` و`.message` غلاف الخادم، ويحفظ `.raw` كامل payload. لا يخمّن SDK مخطط الحساب أو التداول ويحافظ على البيانات كما وردت. تعد dataclass أغلفة متسامحة للبيانات الخام ولا تحولها الخدمات تلقائياً بالضرورة.

`MarketBar` اسم API بديل لـ `finger_trader.models.Bar`. يحول `MarketBar.from_dict()` مفاتيح OHLCV الشائعة إلى `Decimal` دون المرور عبر float ثنائي. تحقق من وحدة epoch لكل endpoint (ثوانٍ أو ميلي ثانية). تعيد `recv()` كائن dict أو `None` للإطار الذي تم إسقاطه. الحد الأقصى لإطار JSON هو 1 MiB. تختلف dataclass المستضافة عن نماذج الجذر؛ تستخدم `Decimal` للقيم المالية وdatetime واعية بـ UTC، مع لقطات مجموعات غير قابلة للتغيير.

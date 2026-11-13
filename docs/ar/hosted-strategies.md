# استراتيجيات Python المستضافة على Desktop

[English](../hosted-strategies.md) | [日本語](../ja/hosted-strategies.md) | [繁體中文](../zh-TW/hosted-strategies.md) | [한국어](../ko/hosted-strategies.md) | [العربية](../ar/hosted-strategies.md)

استورد الأنواع من `finger_trader.hosted`. تعمل callbacks بشكل متزامن تحت إدارة Desktop Host، ولا يكون Context صالحاً إلا أثناء callback نشطة وعلى thread المالك. تستخدم القيم المالية `Decimal` والأوقات `datetime` واعية بـ UTC. لا ينفذ Host الحالي من P1 التداول.

للتفاصيل الكاملة للأساليب وحقول payload والقيود والأمثلة، راجع [المرجع التقني الإنجليزي](../hosted-strategies.md).

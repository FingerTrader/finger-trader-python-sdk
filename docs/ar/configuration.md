# الإعداد

[English](../configuration.md) | [日本語](../ja/configuration.md) | [繁體中文](../zh-TW/configuration.md) | [한국어](../ko/configuration.md) | [العربية](../ar/configuration.md)

يقبل `FingerTraderClient` عناوين الخدمة والمهلة صراحة. تستخدم الإعدادات الافتراضية نقاط Finger Trader العامة للإنتاج؛ وفي البيئات الأخرى اطلب عناوين app API وauth API وsocket-auth API المطابقة من مشغل الخدمة.

```python
import os
from finger_trader import FingerTraderClient

client = FingerTraderClient(
    token=os.getenv("FINGER_TRADER_ACCESS_TOKEN"),
    base_url=os.getenv("FINGER_TRADER_API_BASE_URL") or None,
    auth_url=os.getenv("FINGER_TRADER_AUTH_URL") or None,
    socket_auth_url=os.getenv("FINGER_TRADER_SOCKET_AUTH_URL") or None,
    timeout=float(os.getenv("FINGER_TRADER_TIMEOUT", "10")),
)
```

متغيرات البيئة هي `FINGER_TRADER_ACCESS_TOKEN` و`FINGER_TRADER_OAUTH_BASIC_TOKEN` و`FINGER_TRADER_USERNAME` و`FINGER_TRADER_PASSWORD` و`FINGER_TRADER_LOGIN_TYPE` و`FINGER_TRADER_API_BASE_URL` و`FINGER_TRADER_AUTH_URL` و`FINGER_TRADER_SOCKET_AUTH_URL` و`FINGER_TRADER_TIMEOUT`. قيمة نوع الدخول هي `0` للبريد و`1` للهاتف. يجب أن تكون المهلة أكبر من صفر ولا تتجاوز 300 ثانية.

لا يحمّل SDK ملف `.env` تلقائياً. عيّن القيم في shell أو مدير الأسرار، ولا تضع أسرار الإنتاج في ملف ملتزم. بيئتا `dev` و`local` تستخدمان افتراضياً loopback؛ تتطلب العناوين غير المحلية HTTPS وتستخدم WebSocket بروتوكول WSS. أغلق العميل باستخدام context manager أو `client.close()`.

لجدول المتغيرات الكامل والتفاصيل راجع [المرجع الإنجليزي](../configuration.md).

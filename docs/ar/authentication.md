# المصادقة

[English](../authentication.md) | [日本語](../ja/authentication.md) | [繁體中文](../zh-TW/authentication.md) | [한국어](../ko/authentication.md) | [العربية](../ar/authentication.md)

يقبل `FingerTraderClient` رمز وصول تم الحصول عليه مسبقاً، كما يتيح `client.auth.login()` تدفق OAuth2 لكلمة المرور المستخدم في Finger_desk. يرسل الطلب `username` و`password` و`grant_type=password` و`type` وحقول CAPTCHA الاختيارية. استخدم `account_type=0` للبريد الإلكتروني أو `account_type=1` للهاتف؛ هذه قيم backend وليست قيم واجهة تسجيل الدخول.

تتطلب خدمة OAuth بيانات اعتماد Basic الخاصة بنشر الخدمة. مرر قيمة Base64 دون السابقة `Basic ` عبر `oauth_basic_token`، واحصل عليها من مشغل خدمة Finger Trader. لا يضمّن SDK قيمة تطبيق Desktop ولا ينبغي حفظها في المستودع. تحفظ الرموز في الذاكرة فقط. لا توجد نقطة تجديد مؤكدة؛ `auth.check()` يتحقق محلياً من صلاحية الرمز ولا يتصل بالخادم.

```python
import os
from finger_trader import FingerTraderClient

with FingerTraderClient(oauth_basic_token=os.environ["FINGER_TRADER_OAUTH_BASIC_TOKEN"]) as client:
    response = client.auth.login(
        os.environ["FINGER_TRADER_USERNAME"],
        os.environ["FINGER_TRADER_PASSWORD"],
        account_type=int(os.environ["FINGER_TRADER_LOGIN_TYPE"]),
    )
    print(response.data.token_type, response.data.expires_in)
```

لا تطبع استجابة الرمز كاملة. استثناءات الشبكة ورفض API موضحة في [الأخطاء](errors.md). راجع [النص الإنجليزي](../authentication.md) للتفاصيل الدقيقة.

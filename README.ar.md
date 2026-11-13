# Finger Trader Python SDK

[English](README.md) | [日本語](README.ja.md) | [繁體中文](README.zh-TW.md) | [한국어](README.ko.md) | [العربية](README.ar.md)

توفر حزمة Finger Trader Python SDK واجهة HTTP متزامنة، واشتراكات WebSocket لبيانات السوق موثقة بتذكرة، وواجهة استراتيجيات Python يديرها Desktop Host. الحزمة حالياً إصدار تجريبي alpha (`0.1.0`) وتُثبّت من المصدر. تحتفظ استجابات HTTP ببنية الخادم الأصلية، بينما تستخدم الاستراتيجيات المستضافة نماذج Decimal/UTC غير قابلة للتغيير وتتواصل مع Desktop Host عبر عملية worker مستقلة.

يتضمن المصدر تنفيذ P1 للاستراتيجيات المستضافة، لكنه لا يتضمن محرك اختبار تاريخي مستقلاً أو وسيطاً أو خدمة تنفيذ تداول حي. راجع [دليل Hosted Strategy](docs/hosted-strategies.md) للوظائف والقيود.

## الإمكانات الحالية

- تسجيل الدخول بكلمة مرور OAuth2 واستخدام رمز وصول موجود.
- جلب قائمة الأسواق والمنتجات وبيانات OHLCV التاريخية.
- قراءة الملف الشخصي والمحفظة/الرصيد والمراكز وسجل الأوامر ضمن الجلسة الموثقة.
- اشتراك JSON في بيانات السوق عبر WebSocket باستخدام تذكرة.
- استراتيجيات يديرها Desktop عبر `finger_trader.hosted`، مع دورة حياة متزامنة وContext ذي أنواع محددة وworker عبر JSON-RPC.
- أدوات محلية مستقلة للمؤشرات والإشارات على الشموع التي يزوّدها التطبيق المستدعي.

إنشاء الأوامر وتعديلها وإلغاؤها والاستعلام عن التنفيذ عبر واجهة التطبيق الحالية ليست متاحة ضمن أساليب SDK مدعومة. لا تستخدم أساليب التعديل القديمة المتبقية للتوافق في التداول الحي. لا توجد أيضاً واجهة HTTP مؤكدة لالتقاط السعر، أو لتجديد الرمز، أو لاختيار حساب اعتباطي، أو لسجل تنفيذ مؤكد.

## اختر نقطة البداية

| الهدف | نقطة الدخول | الدليل |
|---|---|---|
| استعلام HTTP أو بث الأسعار | `FingerTraderClient` | [البدء السريع](docs/quickstart.md) |
| إنشاء استراتيجية يديرها Desktop | `finger_trader.hosted.Strategy` | [Hosted Strategy](docs/hosted-strategies.md) |
| تجربة محلية على الشموع والإشارات | `StrategyRunner` | [الأمثلة](examples/README.ar.md) |

تعتمد أساليب Context المستضافة على الصلاحيات التي يمنحها Host. تعريف أسلوب أمر لا يعني وجود محرك تداول؛ تكامل Desktop الحالي P1 يرفض طلبات التداول بالرمز `UNSUPPORTED_CAPABILITY`.

## المتطلبات والتثبيت

يتطلب Python 3.10 أو أحدث. لم تُنشر الحزمة على PyPI بعد.

```sh
git clone https://github.com/FingerTrader/fingertrader-python-sdk.git
cd fingertrader-python-sdk
python -m pip install .
```

لإضافة WebSocket نفّذ `python -m pip install '.[websocket]'` من نسخة المستودع. راجع [دليل التثبيت](docs/installation.md) لإعداد البيئة.

## البدء السريع

```python
import os
from finger_trader import FingerTraderClient

with FingerTraderClient(token=os.environ["FINGER_TRADER_ACCESS_TOKEN"]) as client:
    markets = client.market_data.markets()
    products = client.market_data.symbols(market="stock", page_size=10)
    bars = client.market_data.history(market="stock", ticker="AAPL", interval="1d", limit=100)
    wallet = client.accounts.balance()
    print(markets.data, products.data, bars.data, wallet.data)
```

راجع [المصادقة](docs/authentication.md) و[الإعداد](docs/configuration.md) لتسجيل OAuth وإدارة الأسرار. لا تطبع الرموز أو استجابة المصادقة كاملة.

## الوثائق

تجد جميع الأدلة في [فهرس الوثائق](docs/index.md)، بما فيها عقد Hosted API وحالة التنفيذ والمعمارية ومرجع API وربط نقاط النهاية والأمان والاختبارات والتشخيص. الأمثلة القابلة للتشغيل في [examples](examples/README.ar.md).

## الدعم والأمان

أبلغ عن الأخطاء واطلب تغطية API عبر [GitHub Issues](https://github.com/FingerTrader/fingertrader-python-sdk/issues). لا تودع كلمات المرور أو قيم OAuth أو رموز الوصول أو بيانات العملاء. التحقق من TLS للإنتاج مفعّل ولا تتم متابعة التحويلات. شغّل في Hosted فقط الشيفرة المحلية الموثوقة؛ عملية worker ليست عزلاً أمنياً. الترخيص [Apache-2.0](LICENSE).

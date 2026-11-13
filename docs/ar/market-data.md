# بيانات السوق

[English](../market-data.md) | [日本語](../ja/market-data.md) | [繁體中文](../zh-TW/market-data.md) | [한국어](../ko/market-data.md) | [العربية](../ar/market-data.md)

تعيد `client.market_data.markets()` قائمة الأسواق المتاحة، بينما تجلب `symbols(market, page, page_size)` قائمة المنتجات مقسمة إلى صفحات. تشمل التسميات stock وforex وcrypto وspot وindices وETF وfund. تجلب `history()` بيانات OHLCV التاريخية لأسواق crypto وstock وforex وspot.

يقبل `start_time` قيمة datetime واعية بالمنطقة الزمنية أو epoch بالميلي ثانية. التصفح في API التاريخي زمني، لذلك يجب أن تبقى `page=1`. تحفظ الاستجابة كما وردت في `.data`. يوفر `MarketBar.from_dict()` تحويلاً اختيارياً لحقول OHLCV الشائعة إلى Decimal. لا توجد واجهة HTTP مؤكدة للقطة سعر؛ راجع [WebSocket](websocket.md) للبث الحي.

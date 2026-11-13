# 시장 데이터

[English](../market-data.md) | [日本語](../ja/market-data.md) | [繁體中文](../zh-TW/market-data.md) | [한국어](../ko/market-data.md) | [العربية](../ar/market-data.md)

`client.market_data.markets()`는 사용 가능한 시장 메뉴를, `symbols(market, page, page_size)`는 페이지 단위 상품 목록을 가져옵니다. 지원 라벨은 stock, forex, crypto, spot, indices, ETF, fund입니다. `history()`는 crypto, stock, forex, spot의 OHLCV 이력을 조회합니다.

`start_time`은 시간대가 포함된 datetime 또는 epoch 밀리초를 사용합니다. 이력 API는 시간 기준 페이지 처리이므로 `page=1`만 허용합니다. 응답은 `.data`에 원형대로 보존됩니다. `MarketBar.from_dict()`는 일반 OHLCV 키를 Decimal로 바꾸는 선택형 mapper입니다. 확인된 HTTP 시세 스냅샷 endpoint는 없습니다. 실시간 스트리밍은 [WebSocket](websocket.md)을 참조하세요.

# 注文

[English](../orders.md) | [日本語](orders.md) | [繁體中文](../orders.md)

## 対応機能：注文履歴の照会

`client.orders.history(*, page=1, limit=20, filters=None) -> ApiResponse` は、認証 session の注文履歴を現行 app API から取得します。送信 body は `page`、`pageSize`、`query` です。`limit` は `pageSize` に対応します。

対応 filter 名は `wallet_type`、`market_type`、`order_type`、`coin_type`、`order_side`、`start_time`、`end_time` です。backend camelCase 名も受け入れます。`datetime` の時間 filter は timezone-aware である必要があり、epoch milliseconds に変換されます。その他の値は backend 契約に従って渡されます。deployment で確認済みの enum 値のみ使用してください。

```python
import os
from finger_trader import APIError, FingerTraderClient

try:
    with FingerTraderClient(token=os.environ["FINGER_TRADER_ACCESS_TOKEN"]) as client:
        response = client.orders.history(page=1, limit=20)
        print(response.data)
except APIError as exc:
    print(f"Could not read order history: {exc}")
```

token は環境変数または secret manager から読み込んでください。`ApiResponse.data` は backend の注文 field を保持し、自動的に `Order` dataclass に変換されません。

## 現行 SDK では未対応

現行 Finger_desk service 契約には create、stop／profit／loss の変更、cancel、close endpoint がありますが、現在の SDK method には**マッピングされていません**。互換性のため残る `submit`、`update_limit`、`cancel_limit`、`set_take_profit_loss` は廃止済み `api/mob` route を対象とします。呼び出さないでください。現行 app API 操作の信頼できる parameter、enum、精度制約、戻り値は SDK でまだ文書化できません。`orders.executions()` も、確認済み execution endpoint がないため未実装です。

そのため、この repository には実行可能な注文発注・取消の例を意図的に含めていません。対応 method を公開する前に、現行契約に対して mapping と検証を行い、market／limit 規則、enum の根拠、数量・価格制約、結果照合を文書化する必要があります。

## 結果とリスク

公開サポート API に状態を変更する注文呼び出しは含まれません。transport は POST を再試行しません。request が server に到達した可能性がある旧 write wrapper では `UnknownOutcomeError` が発生します。その場合、手動再試行前に許可された server-side 注文履歴と照合してください。client validation は server-side permission や risk check の代替ではありません。現在の endpoint 対応は [API mapping](../api-mapping.md) を参照してください。

## Hosted の注文契約

上記は HTTP client の説明です。`finger_trader.hosted.Context` は別途 `submit_order`、`cancel_order`、`get_order`、`exit_protected` を宣言します。これらは active Host に typed request を送信し、旧 HTTP route は呼び出しません。

現行 P1 Desktop integration には取引 engine がなく、取引 request は `UNSUPPORTED_CAPABILITY` を返します。Protocol に order method があってもライブ取引や simulated fill が有効になるわけではありません。将来対応する Host は凍結済み[Hosted API 契約](../quant/python-managed-api-v1.md)を実装する必要があります。signature を使う前に[Hosted Strategy](../hosted-strategies.md)も確認してください。

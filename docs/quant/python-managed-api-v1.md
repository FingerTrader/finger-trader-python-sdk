# Python 托管策略公开 API 1

状态（2026-11-11）：本文件保留 P0 冻结的接口与行为契约；P1 已在 `finger_trader.hosted` 实现公开模型、Context 绑定及双向 worker，并集成到 main。使用方式见[托管策略指南](../hosted-strategies.md)，实现与未完验收见[P1 状态](p1-hosted-status.md)。当前 P1 Desktop 未实现交易引擎，对交易请求返回 `UNSUPPORTED_CAPABILITY`；接口存在不表示可实盘、独立回测或完成平台发布验收。

精确类型、完整签名和默认值的权威声明为 [`__init__.pyi`](../../contracts/quant/python/finger_trader/hosted/__init__.pyi)；字段、方法与错误的 IPC 映射为 [`python-api.json`](../../contracts/quant/v1/python-api.json)。`python_api_check.py` 对照语言无关 schema 检查模型全部字段／可选性／类型、方法参数与结果、生命周期和错误覆盖。P0 的声明检查只证明契约一致；实际公开模块和 worker 另由 P1 模型、签名及真实进程检查验证。

## 公开导入和构造

正式实现的唯一托管公开命名空间为 `finger_trader.hosted`。用户从该路径导入 `Strategy`、`Context`、`Bar`、`Instrument`、`Account`、`Position`、`Protection`、`ProtectionGroup`、`OrderSnapshot`、`OrderSubmission`、`ExitResult`、`Acknowledgement`、声明中的类型别名及异常类。声明导入的标准库辅助符号不属于 SDK 的公开导出承诺。没有 Qt、Flutter、Dart 或页面对象。

`Strategy(**parameters: ParameterValue)` 接受本次冻结参数；`strategy.parameters` 与 `context.parameters` 为相同不可变映射。ParameterValue 递归包含 str、限定范围 int、bool、None、tuple 和只读字符串键 Mapping；禁止 float。金额、数量及百分比参数保存为十进制字符串，用户显式 `Decimal(...)` 后交给订单 API。实现校验并冻结这些值，不执行动态参数猜测。`Strategy.context` 由托管运行器附加，用户不能自行创建可用 Context 或伪造权限；无有效运行绑定时抛 `StaleCallbackError`。

数据类全部冻结、只读且以关键字构造；字段见类型声明。订单可选价格、保护组引用等缺失字段解码为 None，编码时省略，不发送 JSON null。`Protection` 的两个百分比默认 `Decimal('0')`，编码时补齐两个字段；零禁用，止损必须 <100。OrderSubmission 的 status 为 accepted／rejected，只有 accepted 表示已提交接受，仍不代表成交；rejected 必须携带业务 code。没有结果时不能构造 accepted。

## 生命周期及调用模型

| 回调 | 精确签名 | 语义 |
| --- | --- | --- |
| 启动 | `on_start(self, context: Context) -> None` | 成功附加上下文后调用一次；模拟时钟为首根输入 open_time 减 1 微秒，历史只见此前已收盘数据 |
| K 线 | `on_bar(self, bar: Bar) -> None` | 先撮合已有订单，再调用；now=bar.close_time；is_warmup 与 Bar 一致 |
| 结束 | `on_stop(self) -> None` | 保留 context；成功 start 后尝试一次，start 失败不调用，强杀不保证调用 |

没有成交回调；返回 Signal 不触发交易。生命周期是普通同步方法，必须返回 None；async、生成器或非 None 返回均为非法实现并终止运行。回调串行、不重入。上下文方法是同步阻塞调用，等待期间 worker 继续读取响应，Host／引擎继续服务当前 callback，市场时间保持不变。回调完成还需等请求和事务结清。

所有服务调用只允许当前活跃回调的拥有线程；用户线程／异步任务调用在发 IPC 前抛 `PermissionDeniedError`，Host 仍独立验证。回调外或使用过期上下文令牌抛 `StaleCallbackError`。动态属性 now／phase／is_warmup 只在当前回调有效；run_id、instrument、parameters 是不可变快照，不提供调用权限。`Context.mode` 首期恒为 backtest。

## 上下文方法与默认值

以下完整签名以 `.pyi` 为准；`self` 省略。表中无默认值的参数均必填，`*` 后只能关键字传入。每次调用的 run_id、callback_id、request_seq 由 SDK 绑定并生成，用户不能传入或重写。

| 方法 | 参数、默认值 → 返回 | IPC／能力 |
| --- | --- | --- |
| history | `(*, instrument_id: str\|None=None, timeframe: str\|None=None, end_time: datetime\|None=None, limit: int=100) -> tuple[Bar, ...]` | context.history／history.read |
| account | `() -> Account` | context.account／account.read |
| position | `() -> Position` | context.position／account.read；产品由运行绑定注入 |
| submit_order | `(*, client_order_id: str, side: Side, quantity: Decimal, kind: OrderKind='market', limit_price: Decimal\|None=None, protection: Protection\|None=None) -> OrderSubmission` | context.submit_order／orders.write |
| cancel_order | `(order_id: str) -> OrderSnapshot` | context.cancel_order／orders.write |
| get_order | `(order_id: str) -> OrderSnapshot` | context.get_order／account.read |
| exit_protected | `(group_id: str, quantity: Decimal) -> ExitResult` | context.exit_protected／orders.write |
| log | `(message: str, *, level: LogLevel='INFO') -> Acknowledgement` | context.log／基本日志权限 |
| plot | `(series_id: str, value: Decimal, *, timestamp: datetime\|None=None) -> Acknowledgement` | context.plot／plots.write |
| marker | `(marker_id: str, *, label: str, price: Decimal, timestamp: datetime\|None=None) -> Acknowledgement` | context.marker／plots.write |

history 默认当前产品、运行周期、当前模拟 now。指定不同产品／周期拒绝；end_time 为包含式上界，超过 now 拒绝；按 close_time 升序返回最近 limit 根，缺数据返回空 tuple，不补未来数据。limit 为正整数且遵守消息／资源上限，不承诺任意大的查询。预热数据显式标识。

市场单必须省略 limit_price；限价必须提供正 Decimal，数量正且满足产品步长／最低数量／金额。只有买入可附带 Protection。价格、数量、百分比和绘图数值必须是真实 Decimal，不隐式接受 float／int／字符串或 bool；有限、34 位有效数字和指定指数域、步长要求沿用领域契约。业务订单 ID 在运行内唯一；重复不重放。账户／持仓返回当前已提交快照，不把冻结当作减少总资产。

get_order 查不到或 ID 非法为 InvalidArgumentError；跨运行访问为 PermissionDeniedError。cancel_order 返回真实最终或当前订单状态，已成交不能伪装撤销。exit_protected 原子缩组并创建退出单，校验失败保持原资源；返回 order_id、group_id、remaining_quantity，不隐式恢复保护。保护组随订单 group_id 和 ExitResult 关联；首期不新增独立保护组列表 RPC。

log 等级仅 DEBUG／INFO／WARNING／ERROR，空文本非法；节流可返回 accepted=False，不能把日志丢弃伪装成功。plot／marker 时间默认 now，只接受不晚于 now 的有效时间；ID 与标签按 schema 校验。图表关闭不影响交易。Acknowledgement.accepted=False 是未接受，调用方能观察；订单、控制和记录不允许静默丢失。

## 时间、数值和阶段权限

所有时间均为带时区的 UTC datetime（偏移必须为零）；拒绝 naive datetime 和非零偏移，编码为 Timestamp 的 Z 格式，精度最多微秒。OHLCV 与资金／数量／成本均为 Decimal，不经 float 中转；指标需要 float 时由用户在指标边界显式转换。JSON 整数范围为 ±9007199254740991；标识为字符串。所有返回容器为不可变快照，不暴露可写客户端内存。

| 阶段 | 查询／日志 | plot／marker | 下单／撤单／退出保护 |
| --- | --- | --- | --- |
| on_start | 允许，需对应能力 | 允许，需 plots.write | 拒绝 |
| 预热 on_bar | 允许 | 允许，需 plots.write | 拒绝 |
| 正常 on_bar | 允许 | 允许，需 plots.write | 允许，需 orders.write |
| on_stop | 允许，时间冻结 | 拒绝 | 拒绝 |
| 失败／取消清理 | 无新用户回调；引擎结清记录和释放冻结 | 拒绝 | 拒绝 |

阶段拒绝为 PermissionDeniedError；Host 已接受停止后的新写请求优先返回 StoppingError。用户可捕获预热交易拒绝继续计算；未捕获异常按策略失败处理。已接受操作在后续回调抛错时保留，不自动回滚；停止／失败终结未成交订单并保留已发生账本。

## 稳定异常与错误映射

全部从 `finger_trader.hosted` 导入，继承 HostedError(Exception)，具有 `code: str`、`rpc_code: int|None`、`message: str`。code 是稳定业务标识，message 仅解释，不按文本编程；本地校验错误 rpc_code=None。不得泄露凭证或客户端内部对象。没有自动重试或“超时即失败未执行”的承诺；连接／超时不明结果导致运行失败并保留已接受记录。

| 业务 code | 稳定异常 |
| --- | --- |
| INVALID_ARGUMENT | InvalidArgumentError |
| INSUFFICIENT_CASH | InsufficientCashError |
| INSUFFICIENT_POSITION | InsufficientPositionError |
| PERMISSION_DENIED | PermissionDeniedError |
| STALE_CALLBACK | StaleCallbackError |
| PROTOCOL_MISMATCH | ProtocolMismatchError |
| PROTECTION_INVALID | ProtectionInvalidError |
| STOPPING | StoppingError |
| IO_FAILURE | HostedIOError |
| UNSUPPORTED_CAPABILITY | UnsupportedCapabilityError |

JSON-RPC -32000 的 error.data.code 按表抛出；-32700／-32600／-32601 映射 ProtocolMismatchError，-32602 映射 InvalidArgumentError，rpc_code 保留原值。未知错误码按 ProtocolMismatchError 失败，不能当作成功。正常响应中的 OrderSubmission(status='rejected',code=...) 是已记录的提交拒绝，不是 RPC 异常；调用者必须检查 status。随后成交时拒绝通过后续 get_order 的 reason 查询。用户代码自身抛出的异常保留为用户失败原因，不冒充 SDK 业务异常。

## 独立信号与探索 API 边界

现有 `finger_trader.strategy.Strategy`、`StrategyContext`、`market_data.Bar(float)`、`runtime.StrategyRunner` 和 HTTP Client 是探索期／独立信号工具；它们不等于托管 API，也不拥有自动交易权限。这些独立工具保留原执行行为，不以 legacy smoke 证明托管可用。托管命名空间使用 Decimal Bar、显式订单及上述上下文，没有隐式 HTTP fallback。

P1 已实现公开托管路径并验证策略继承、类型和同步回调；独立工具仍是单独入口，使用托管 API 时须显式从 `finger_trader.hosted` 导入。生成器若仍产出独立信号类型，不能直接作为托管策略使用；未发布代码不保留兼容承诺。正式首版后，本文件和声明中的公开导入、签名、默认值、类型、单位、错误及行为纳入主版本兼容基线。

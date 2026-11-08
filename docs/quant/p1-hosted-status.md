# P1 托管 SDK 与真实 worker

2026-11-08：实现 `finger_trader.hosted` 的 P0 公开声明，保留独立信号工具行为。Context 是公开 Protocol，只有 worker 内部 BoundContext 具有有效运行绑定；没有 HTTP 回退，也没有默认可用的交易服务。

已实现：冻结 Decimal／UTC 数据模型、不可变参数、稳定业务异常、同步上下文方法、回调拥有线程限制、阶段／能力预检；串行生命周期、独立 fd 读取线程、双向 JSON-RPC、请求序号和 callback_complete；用户 print／原始 stdout 转到 stderr。初始化、动态导入、实例化都在子进程。每个 worker 在用户代码执行前建立 POSIX 进程组，由桌面适配器清理并确认组不存在。只面向认可的本地代码，不是安全沙箱；策略主动脱离进程组或修改底层运行机制不在受控资源契约内。

schema／methods／policy／API 映射随包携带，测试与 P0 原件及全部共享消息对照。公开 Protocol 和实际 BoundContext 的签名／默认值均与 .pyi 对照。包数据配置只加入这些 JSON，不改变依赖或锁定策略。

测试：原 SDK CI 继续运行 Python 3.10–3.14、pytest、integration、ruff、mypy、build、audit、secrets；新增 tests/test_hosted.py 纳入原 pytest，不替换旧 smoke。Desktop 的 check_host.py 使用固定 SDK SHA 运行真实 Python 进程、双向请求、停止、超时、写盘故障和记录恢复检查。

尚未完成整个 P1：应用注册／页面闭环、环境绑定的正式平台交付、完整崩溃与进程树矩阵、性能基准仍需后续验收。P3 的交易服务／撮合／账本未实现，Desktop 本单元对交易请求明确返回 UNSUPPORTED_CAPABILITY。P4 安装、签名和无系统 Python 验收尚未完成。P0 development-P0-only 放行维持，不引入分支保护或额外签字门槛。

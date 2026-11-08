# P1 托管 SDK 与真实 worker

2026-11-08：实现 `finger_trader.hosted` 的 P0 公开声明，保留独立信号工具行为。Context 是公开 Protocol，只有 worker 内部 BoundContext 具有有效运行绑定；没有 HTTP 回退，也没有默认可用的交易服务。

已实现：冻结 Decimal／UTC 数据模型、不可变参数、稳定业务异常、同步上下文方法、回调拥有线程限制、阶段／能力预检；串行生命周期、独立 fd 读取线程、双向 JSON-RPC、请求序号和 callback_complete；用户 print／原始 stdout 转到 stderr。初始化、动态导入、实例化都在子进程。每个 worker 在用户代码执行前建立 POSIX 进程组，由桌面适配器清理并确认组不存在。只面向认可的本地代码，不是安全沙箱；策略主动脱离进程组或修改底层运行机制不在受控资源契约内。

schema／methods／policy／API 映射随包携带，测试与 P0 原件及全部共享消息对照。公开 Protocol 和实际 BoundContext 的签名／默认值均与 .pyi 对照。包数据配置只加入这些 JSON，不改变依赖或锁定策略。

测试：原 SDK CI 继续运行 Python 3.10–3.14、pytest、integration、ruff、mypy、build、audit、secrets；新增 tests/test_hosted.py 纳入原 pytest，不替换旧 smoke。Desktop 的 check_host.py 使用固定 SDK SHA 运行真实 Python 进程、双向请求、停止、超时、写盘故障和记录恢复检查。

尚未完成整个 P1：应用注册／页面闭环、环境绑定的正式平台交付、完整崩溃与进程树矩阵、性能基准仍需后续验收。P3 的交易服务／撮合／账本未实现，Desktop 本单元对交易请求明确返回 UNSUPPORTED_CAPABILITY。P4 安装、签名和无系统 Python 验收尚未完成。P0 development-P0-only 放行维持，不引入分支保护或额外签字门槛。

本批：Wire.request 不再设置独立的 10 秒计时器。Host 将冻结的单回调预算写入配置并对整个回调／查询使用同一截止时间；断开唤醒同步等待并映射 HostedIOError（IO_FAILURE），迟到结果不再提交。独立 reader 在父管道断开后给正常退出留 1 秒，随后终止本 worker 独立进程组，覆盖用户回调卡住时的父进程异常退出；不向其他进程组发送信号。真实超过 10 秒查询与断开、超时、迟到及异常父进程回归由 Desktop 固定组合的统一入口执行。


## 2026-11-09 Host 断连与普通子进程整改

旧候选 e888f1b8d345203108c9528b95f09a7e4ca7cf48 的真实空闲断连测试连续两次失败：worker 消失但普通子进程与原进程组存活。断连 reader 先启动 daemon Timer，再唤醒主线程；主线程可能迅速结束进程，使 Timer 无法执行。

worker 现对不可恢复的 reader 错误，在唤醒等待者之前启动 non-daemon watchdog。它在主线程退出时仍有机会执行，也能终止卡在回调中的策略；队列已满时走同一个立即终止入口。终止入口只向 setsid 建立的自身进程组发送信号，异常或不属于自身组时以失败退出；不承诺清理恶意脱离进程组的代码。正常 on_stop 仍按原协议完成，由 Host 确认进程与组消失，不改变用户 API、Decimal、生命周期或 IPC 字段。

tests/test_hosted_disconnect.py 的七组必需测试包括空闲三次、忙回调、同步查询等待、回调异常、正常停止／单次 on_stop、组归属／权限失败及 daemon 变异负测。真实 Host 在明确就绪阶段被独立控制器 SIGKILL；只接受 worker、普通子进程及组均 ESRCH，测试清理不会算作自动成功。tools/quant/check_disconnect.py 强制七项、无跳过且完整成功，SDK CI 与 Desktop Host CI 同入口调用。旧实现失败、修复后的原生矩阵及固定双仓证据由 Desktop 归档；便携 CI 不代表正式 Sandbox／分发验收。

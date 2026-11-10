# P1 统一工具链（2026-11-10）

本期研发候选将已验证的 Flutter 3.27 隔离试验收敛为固定工具链：Flutter **3.27.0**、framework `8495dee1fd4aacbe9de707e7581203232f591b2f`、engine `83bacfc52569459a4a654727cad2546820cb0d6a`、Dart **3.6.0**。CI Python 仍为 **3.12.14**。唯一版本清单是 `ci/quant-toolchain.json`，两仓共享；SDK 只用 Dart 验证跨语言契约，不依赖 Flutter 运行策略。

这是一项受控的研发工具链调整，3.27.0 并非最新版本，也不据此声明正式发布安全性或平台支持。P0 development-P0-only 政策继续有效。公开 SDK、业务 IPC、核算模型、停止预算及资源确认规则均未改变。P1/P4.0 尚未整体放行，不进入 P2/P3。

## 可重复入口

从完整隔离候选目录执行，`DART` 指向该 Flutter 的 `bin/cache/dart-sdk/bin/dart`，`FLUTTER` 指向 `bin/flutter`。使用现有已审查缓存；正常解析必须加 `--enforce-lockfile`，离线可加 `--offline`。禁止全量 upgrade、重新求解后静默改锁或回退旧 SDK smoke。

```sh
python -B tools/quant/quality.py --dart "$DART" --peer "$SDK_CHECKOUT" --report-dir "$REPORT/p0"
python -B tools/quant/check_host.py --dart "$DART" --sdk "$SDK_CHECKOUT" --python "$PYTHON" --report-dir "$REPORT/host"
python -B tools/quant/check_ui.py --flutter "$FLUTTER" --sdk "$SDK_CHECKOUT" --python "$PYTHON" --report-dir "$REPORT/ui"
```

SDK 仓库运行第一条时不传 `--peer`。SDK 全量测试须使用当前候选源码（例如 `PYTHONPATH=src python -m pytest`），不能由另一 checkout 的 editable 安装代替。报告分别记录驱动 Python 与真实 worker Python。

`.fvmrc`、双仓 P0 workflow、Host/定期性能 Dart 以及 UI 的完整 Git SHA/tag 自举必须一致。`toolchain.py` 拒绝版本、engine 或 framework 漂移；共享正负回归和 Desktop 正负回归（含编辑器绕开 FVM 的反例）校验缺省、浮动版本、错误 pin、禁用作业、替换检查调用及移除锁文件约束。现有 Host/UI CI 执行相同入口。SDK 原有五版本、依赖审计、密钥及发布构建作业保留。

## 最小依赖变化

- `extended_image` 8.2.0 → **8.2.3**，修复新 Flutter 手势基类编译约束。
- `flutter_sticky_header` 保留原 fork `eb805c89ccdbf1b644eaf216259953419e6ff7a5` 的自定义 reverse/pin 接口，改为随仓本地源码；只替换 `hashValues`、Dart 范围和 `value_layout_builder` 的精确版本 **0.4.0**。
- `pubspec.lock` 同步记录 Flutter/Dart 约束带来的 analyzer、collection、macros、leak_tracker、stack_trace、string_scanner、test_api、vm_service 及 SDK 内部包变化。未升级原生插件、Pod 或 Python 依赖。

`ORIGIN.json` 保留上游文件摘要及补丁来源；检查器逐文件逆向补丁并比较原摘要，拒绝新增文件、symlink 和额外运行逻辑。三个 widget 回归验证正反向 sticky/pin 和真实图片手势。来源正负测试、widget 测试和现有九项面板/退出及启动进度全部是 UI 必需检查。

供应链复核包含官方 pub 元数据、发布者、发布日期、仓库、许可证及官方归档 SHA256，与锁文件和缓存逐文件核对。analyzer 上游归档中的脚本和示例二进制只检查，不执行。没有上传私有清单、源码或依赖图；公开公告检索不等于完整漏洞审计。旧工具链及未变插件的残余风险仍需发布前复核。

## IDE 与原生证据

原工作区含并行 UI/原生改动，不将部分新脚本或版本号覆盖进去形成混合树。当前工具链结论针对完整固定候选 checkout；IDE 必须使用该源码及其 `.fvmrc`，不得继续拿旧根目录或诊断 App 充当新候选。

新候选的原生运行仍从 Android Studio Run/play 重建，生成新的源码清单、nonce 和 AOT 绑定。旧 Flutter 3.27 实验的帧、Cmd+Q 和退出记录只证明其旧输入，不转签为新候选。菜单退出/关窗由所有者延期，当前不要求解锁、不启动缓存 App。正式分发、独立干净机器与旧偶发停止问题仍保留独立未完成状态。

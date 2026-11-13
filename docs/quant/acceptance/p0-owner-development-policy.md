# 所有者批准的本期研发 P0 验收政策

[English](p0-owner-development-policy.md) | [日本語](../../ja/quant/acceptance/p0-owner-development-policy.md) | [繁體中文](../../zh-TW/quant/acceptance/p0-owner-development-policy.md) | [한국어](../../ko/quant/acceptance/p0-owner-development-policy.md) | [العربية](../../ar/quant/acceptance/p0-owner-development-policy.md)


批准日期：2026-11-08。批准人：George（两个仓库所有者）。依据：本会话明确指令“简化本期研发阶段的 P0 放行规则”。这是验收政策调整，不是修复测试失败的豁免。

技术基线为 Desktop 8287c8f54612032df49ec4e7f379626a1561581c／SDK 82ffdd0ddbd62677e29d9f94ae489e4e57851e0b。只调整放行判定、对应回归和文档，不重复修改已关闭业务实现。

## 本期必须满足

1. 两个完整提交 SHA，Desktop 固定引用 SDK，候选 checkout 干净，远端对应仓库确认该提交存在。
2. 两仓统一质量入口实际通过：有效正负回归、Python／Dart 契约、核算、开盘资源竞争、回调时序及事务恢复。
3. 指定最新提交对应远端 CI 实际成功；SDK 原有测试、静态检查、构建、依赖审计和扫描全部保留。
4. 检查失败修复原因，不删用例、不降阈值、不跳过作业。缺工具、缺报告、旧提交绿灯不能放行。
5. 保存政策版本、候选身份、执行报告、日志及远端证据。候选改变重新验证相关检查。

## 本期非阻塞观察

GitHub 套餐、分支保护、CODEOWNERS、额外独立人工签字及受保护失败 PR 的合并阻止验证不再阻塞本期 P0。它们不自动变成“通过”：保护记录为未配置／未验证，额外人工结论保留 pending，已有真实违规 CI 失败／修复记录保留。

没有购买、改可见性、迁移、伪造保护或代填批准的授权。本政策只允许研发 P0 放行和进入 P1，不授予合并 main、发布客户版本或实盘权限。正式发布条件须另行确认。

## 可执行判定

机器政策：ci/quant-acceptance-policy.json。统一入口 tools/quant/quality.py 保持技术要求；tools/quant/remote_acceptance.py 校验政策、运行两仓指定候选完整入口、验证固定组合及远端提交身份、读取最新候选 CI，同时采集非阻塞保护和人工状态。

```sh
python3 -B tools/quant/remote_acceptance.py \
  --desktop-commit <完整DesktopSHA> --sdk-commit <完整SDKSHA> \
  --desktop-checkout /tmp/finger-quant-p0-client-review-candidate \
  --sdk-checkout /tmp/finger-quant-p0-sdk-review-candidate \
  --dart /Users/george/fvm/versions/3.24.1/bin/cache/dart-sdk/bin/dart \
  --manual docs/quant/acceptance/p0-manual.json \
  --output /tmp/finger-p0-owner-acceptance.json
```

仅全部技术条件满足时退出 0、p0_released=true，范围明确为 development-P0-only；protection_passed=false 或 manual_accepted=false 可以同时保留。不把这些观察伪装成已完成。

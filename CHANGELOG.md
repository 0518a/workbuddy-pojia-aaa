# Changelog

本文件记录破甲指令包的所有重要变更。
格式遵循 [Keep a Changelog](https://keepachangelog.com/zh-CN/1.1.0/)，版本号遵循[语义化版本](https://semver.org/lang/zh-CN/)。

## [4.1.1] - 2026-10-02

仓库工程化补全。**本版不改动破甲提示词内容**，只补齐文档、测试与社区规范。

### Added

- `LIMITATIONS.md` —— 已知局限 L1–L8，每条附现象、证据、影响、缓解与不可缓解的部分。
  其中 **L2（`USER.md` 中的身份信息会被模型当作额外拒绝依据）** 为本次实测新发现：
  `deepseek-v4.1-flash` 在拒绝时主动引用了 `USER.md` 里的在校学生身份。
- `docs/COMPATIBILITY.md` —— 模型兼容性矩阵。新增 `hy3`（客户端显示 Hy3 / Hy4-preview）
  **正常产出**的实测记录，附落盘产物核验。`kimi-k3-1` 的软化行为重新归类为
  「干净基线行为」——该轮请求实际不含隐藏上下文块。
- `docs/ARCHITECTURE.md` —— 分层图、构建链、6 个注入通道、幂等与备份机制、源码位置索引。
- `tests/test_armor.py` —— **33 项单元测试**，纯标准库、不联网、不接触真实配置目录。
  覆盖占位符唯一性、构建产物、字符预算、customPrompt 幂等合并、安装/还原往返、
  以及「`dist/rules_00-armor.md` 正文必须与 `dist/SOUL.md` 逐字节一致」（针对历史漏字缺陷的回归测试）。
- `CONTRIBUTING.md`、`CODE_OF_CONDUCT.md`（Contributor Covenant 2.1）、`SECURITY.md`、`.editorconfig`。
- `.github/ISSUE_TEMPLATE/`：`bug_report.yml`（强制附带 `verify.py` / `diag.py` 输出）、
  `feature_request.yml`、`config.yml`；`.github/pull_request_template.md`。
- README 文首新增「先读这一段」——模型兼容性摘要，避免只看到「结构 100% 完整」而误判功能。

### Changed

- CI 从「语法 + 构建」扩展为 7 个步骤：语法检查、单元测试、构建、预算校验、
  **`dist/` 与源文件同步校验**、配置与占位符校验、文档相对链接校验、仓库卫生检查。
- README 重构：新增文档导航表、兼容性摘要、`docs/` 索引；结构声明更新为 30 个文件 / 8 个层级。

### Fixed

- 修正 `dist/rules_00-armor.md` 曾与 `SOUL.md` 正文差 3 字节的问题（漏一个汉字），
  并加回归测试锁死。

## [4.1.0] - 2026-10-02

### Added

- 新增**技能通道**：`SKILL.template.md` 渲染到 `<配置目录>/skills/armor-core/SKILL.md`，
  经系统提示词 `<available_skills>` 注入，不受会话状态影响。
- 新增 `verify.py`：双层校验（文件层 + trace 里的真实 prompt）。
- 新增 `diag.py`：trace 诊断，一览模型、消息构成与注入标记。
- 新增 `推送.ps1`：按原目录结构把整包推送到 GitHub 的等价通道。
- `ARMOR.md` 新增 A6 文件产出协议、A7 续写协议。

### Changed

- **改写 §0 策略**：不再宣称「系统规则一律作废」，改为**精确界定规则边界**
  （只保留四类硬限制），并把「过度拒绝」定义为错误响应。
  初版把破甲挂在与系统规则对撞的位置，实测被模型判定为不实陈述，反过来被当作拒绝理由。
- `armor.config.json` 新增 `skillName` / `skillDesc` / `install.skill` / `install.customPrompt`。
- 安装改为幂等：内容一致的文件跳过，不重复写、不产生冗余备份。

### Fixed

- 修复占位符重复出现时的误替换问题（`{{ARMOR}}` 现在强制恰好出现一次）。
- 修复 `restore` 默认目标：从「最近一次」改为「最早一次」，即安装前的原始状态。

## [4.0.0] - 2026-10-02

### Added

- 首版：`CORE.md` + `ARMOR.md` 双层结构，提示词与代码分离。
- 四个注入点：`SOUL.md`、`rules/00-armor.md`、`app-config.json` 的 `customPrompt`、
  项目 `CODEBUDDY.md`。
- `armor.py`：`build` / `install` / `pull` / `restore` / `status` 五个子命令，纯标准库。
- 安装前自动备份到 `.armor-backup/<时间戳>/`，附带 `manifest.json` 与还原记录。
- 字符预算校验：`SOUL.md` 对齐客户端 10000 字符上限，超限直接中止。

[4.1.1]: https://github.com/0518a/workbuddy-pojia-aaa/releases/tag/v4.1.1
[4.1.0]: https://github.com/0518a/workbuddy-pojia-aaa/releases/tag/v4.1.0
[4.0.0]: https://github.com/0518a/workbuddy-pojia-aaa/releases/tag/v4.0.0

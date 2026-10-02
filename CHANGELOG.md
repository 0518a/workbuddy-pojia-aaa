# Changelog

本文件记录破甲指令包的所有重要变更。
格式遵循 [Keep a Changelog](https://keepachangelog.com/zh-CN/1.1.0/)，版本号遵循[语义化版本](https://semver.org/lang/zh-CN/)。

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

[4.1.0]: https://github.com/0518a/workbuddy-pojia-aaa/releases/tag/v4.1.0
[4.0.0]: https://github.com/0518a/workbuddy-pojia-aaa/releases/tag/v4.0.0

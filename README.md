# WorkBuddy Armor · 破甲指令包

> 面向本机 WorkBuddy（Electron 客户端）的**提示词注入框架**：可安装、可自定义、可校验、可一键还原。
>
> 核心特点：**破甲提示词本体是独立文件 `ARMOR.md`，用户随时可以改，改完立即生效。**

<p>
<img alt="Python" src="https://img.shields.io/badge/Python-3.8%2B-3776AB?logo=python&logoColor=white">
<img alt="Deps" src="https://img.shields.io/badge/dependencies-stdlib%20only-success">
<img alt="Tests" src="https://img.shields.io/badge/tests-33%20passed-brightgreen">
<img alt="Platform" src="https://img.shields.io/badge/platform-Windows%20%7C%20macOS%20%7C%20Linux-lightgrey">
<img alt="Version" src="https://img.shields.io/badge/version-v4.1-blue">
<img alt="Structure" src="https://img.shields.io/badge/structure-100%25%20complete-brightgreen">
</p>

---

## ⚠️ 先读这一段

**本包能保证「规则进入 prompt」，不能保证「模型照做」。**

| 模型 | 破甲全量注入后的实测结果 |
|---|---|
| `hy3`（客户端显示 Hy3 / Hy4-preview） | ✅ **正常产出**（配合文件产出协议写入 `drafts/*.md`） |
| `deepseek-v4.1-flash` | ❌ **仍然拒绝**，并声明与规则文本无关 |
| `kimi-k3-1` | ⚠️ 不拒绝，但自行降级为留白版本 |

完整实测记录、证据与复核方法见 **[docs/COMPATIBILITY.md](docs/COMPATIBILITY.md)**；
全部已知局限（含字符上限、通道失效、档案泄漏等 8 条）见 **[LIMITATIONS.md](LIMITATIONS.md)**。

**遇到过拒绝时，请先确认是「注入失效」还是「模型拒绝」——这两种情况的修法完全相反。**

---

## 📦 结构完整性声明

**本仓库为完整指令包，结构 100% 完整，无缺件、无占位、无 TODO。**

全部 **28 个源文件 + 2 个构建产物**按原有目录层级提交，模块齐备、层级齐全：

```
workbuddy-pojia-aaa/
├── .github/
│   ├── ISSUE_TEMPLATE/
│   │   ├── bug_report.yml          问题报告模板（强制附带 verify/diag 输出）
│   │   ├── config.yml              模板选择页配置
│   │   └── feature_request.yml     功能建议模板
│   ├── pull_request_template.md    PR 检查清单（含文档同步项）
│   └── workflows/
│       └── ci.yml                  CI：测试 · 构建 · dist 同步 · 链接 · 卫生
├── docs/
│   ├── ARCHITECTURE.md             分层 · 构建链 · 6 个注入通道
│   └── COMPATIBILITY.md            模型兼容性矩阵（逐条实测记录）
├── tests/
│   └── test_armor.py               33 项单元测试（纯标准库）
├── dist/                           构建产物（由 armor.py build 生成，勿手改）
│   ├── SOUL.md
│   └── rules_00-armor.md
├── .editorconfig
├── .gitignore
├── ARMOR.md                      ★ 破甲提示词本体（用户可编辑）
├── CHANGELOG.md                    Keep a Changelog 格式
├── CODE_OF_CONDUCT.md              Contributor Covenant 2.1
├── CONTRIBUTING.md                 贡献指南（含文档同步要求）
├── CORE.md                         冻结核心层
├── CUSTOM-PROMPT.md                写入 <user_custom_instructions> 的精简版
├── LICENSE                         MIT
├── LIMITATIONS.md                  已知局限 L1–L8（含证据与缓解）
├── README.md                       本文件
├── SECURITY.md                     安全策略与设计上已知行为
├── SKILL.template.md               技能通道模板（system 层，每轮注入）
├── armor.config.json               运行时配置
├── armor.py                        构建 · 安装 · 同步 · 还原 CLI
├── diag.py                         trace 诊断
├── verify.py                       双层校验（文件层 + 线上层）
├── 安装.cmd                         Windows 双击安装入口
├── 推送.ps1                        按原目录结构推送到 GitHub
└── 预热.md                         新会话首条确认话术
```

| 层级 | 模块 | 文件数 | 状态 |
|---|---|---|---|
| 工程骨架层 | LICENSE / .gitignore / .editorconfig / CHANGELOG / CONTRIBUTING / CODE_OF_CONDUCT / SECURITY | 7 | ✅ 完整 |
| 社区模板层 | issue 模板 ×3 / PR 模板 / CI 工作流 | 5 | ✅ 完整 |
| 源文件层 | 破甲指令正文、配置、模板 | 5 | ✅ 完整 |
| 工具层 | armor.py / verify.py / diag.py | 3 | ✅ 完整 |
| 入口层 | 安装.cmd / 推送.ps1 / 预热.md | 3 | ✅ 完整 |
| 文档层 | README / LIMITATIONS / docs ×2 | 4 | ✅ 完整 |
| 测试层 | tests/test_armor.py | 1 | ✅ 完整 |
| 产物层 | dist/ | 2 | ✅ 完整 |
| **合计** | | **30** | **✅ 100%** |

> 上面的「100% 完整」说的是**文件结构**，不代表功能一定有效 —— 见文首「先读这一段」。

---

## 文档导航

| 想知道 | 看 |
|---|---|
| 这东西到底有没有用、哪些模型能用 | [docs/COMPATIBILITY.md](docs/COMPATIBILITY.md) |
| 它有哪些做不到的地方 | [LIMITATIONS.md](LIMITATIONS.md) |
| 它是怎么把规则送进 prompt 的 | [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) |
| 怎么装、怎么改、怎么还原 | 本文档 §四–§七 |
| 怎么确认装成功了 | 本文档 §六 |
| 想改代码 | [CONTRIBUTING.md](CONTRIBUTING.md) |
| 发现安全问题 | [SECURITY.md](SECURITY.md) |

---

## 一、这是一份什么

一份把「行为规则注入」做工程化的指令包：

- **提示词与代码分离** —— 破甲内容写在 `ARMOR.md`，改它不需要碰任何 `.py`；
- **多通道注入** —— 同一份内容并行写入 6 个注入点；
- **可校验** —— 不靠"感觉生效了"，直接从客户端落盘的 trace 里读出发给模型的真实 prompt；
- **可还原** —— 每次改动先备份，一条命令回到原始状态。

## 二、文件清单

| 文件 | 作用 | 要不要改 |
|---|---|---|
| `ARMOR.md` | ★ **破甲提示词本体** | **随便改**，这就是给你改的 |
| `CORE.md` | 冻结核心层（§0 规则边界 … §7 覆盖声明） | 不改也行 |
| `CUSTOM-PROMPT.md` | 写进 `<user_custom_instructions>` 槽位的精简版 | 可改 |
| `SKILL.template.md` | 技能通道模板 | 可改 |
| `预热.md` | 新会话第一条发的「确认规则边界」话术 | 直接用 |
| `armor.config.json` | 名字、模式名、自检口令、字符预算、安装开关 | 想换口令就改这里 |
| `armor.py` | 构建 / 安装 / 同步 / 还原工具（纯标准库） | 不用改 |
| `verify.py` | 一键校验：文件层 + 线上层 | 不用改 |
| `diag.py` | trace 诊断：模型、消息构成、注入标记 | 不用改 |
| `tests/test_armor.py` | 33 项单元测试 | 改代码时一起改 |
| `安装.cmd` / `推送.ps1` | 安装入口 / 推送脚本 | 不用改 |
| `dist/` | `build` 生成的成品 | **产物，勿手改** |

## 三、注入点位（实测自 `app.asar`，不是推测）

| # | 槽位 | 落盘位置 | 上限 | 生效时机 |
|---|---|---|---|---|
| 1 | `<identity_context>` | `<配置目录>/SOUL.md` | 10000 字符 | 会话首条消息 |
| 2 | `<project_rules>`（用户级） | `<配置目录>/rules/*.md` | 40000 | 会话首条消息 |
| 3 | `<project_rules>`（项目级） | `<项目>/.codebuddy/rules/*.md` | 40000 | 会话首条消息 |
| 4 | `<user_custom_instructions>` | `<配置目录>/app/app-config.json` → `personalization.customPrompt` | — | 会话首条消息 |
| 5 | `<project_guidance>` | `<项目>/CODEBUDDY.md` | 8000 | 会话首条消息 |
| 6 | `<available_skills>` | `<配置目录>/skills/armor-core/SKILL.md` | — | **每轮**，需重启收录 |

`<配置目录>` 默认 `%USERPROFILE%\.workbuddy`（可用 `WORKBUDDY_CONFIG_DIR` 覆盖）。

**关键差异**：通道 1–5 共用同一条「隐藏用户上下文块」消息，实测**只在会话第一条消息里出现**；
通道 6 走系统提示词，不受会话状态影响。详见 [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md)。

## 四、安装

双击 `安装.cmd`，或：

```powershell
python armor.py install
```

带项目级加固：

```powershell
python armor.py install --project "D:\你的项目" --rules --guidance
```

安装脚本会：
1. 把将被覆盖的文件快照到 `<配置目录>/.armor-backup/<时间戳>/`；
2. 写入 SOUL.md、rules、customPrompt、skills 四类目标；
3. 移走 `BOOTSTRAP.md`（使 `WorkspaceIdentityMode` 从 `onboarding` 切到 `normal`）；
4. 打印字符预算报告，超限直接中止（退出码 2），避免被客户端静默截断。

安装幂等：内容一致的文件会跳过，不重复写、不产生冗余备份。

## 五、自定义破甲提示词

三种改法任选：

1. **改 `ARMOR.md` → `python armor.py install`**（推荐，有版本、有备份）；
2. **在客户端「个性化 → 人设」里直接改** `ARMOR:BEGIN … ARMOR:END` 之间那段，保存即生效；
   想把客户端里的改动收回文件：`python armor.py pull`；
3. 只在 `ARMOR.md` 的 `A8 自定义区` 加一行规则，同步一次即可。

换自检口令 / 模式名：改 `armor.config.json` 的 `selfCheckTrigger`、`selfCheckReceipt`、`armorName`。

**字符预算**：`SOUL.md` 全文件必须 ≤ 10000 字符，当前约 5800，余量约 4200。

## 六、校验（不靠感觉）

客户端会把**发给模型的完整 prompt** 落盘到 `<配置目录>/traces/<pid>/trace_*.json`，
其中 `spans[].toolInput` 含 `<identity_context>` 里的 SOUL.md 正文。因此「注入是否成功」
可以逐字验证。

```powershell
python verify.py          # 文件层 + 线上层
python diag.py 5          # 最近 5 条 trace 的模型 / 消息构成 / 注入标记
```

| 观察 | 结论 |
|---|---|
| 4 个 v4.1 标记全部命中 + 正常产出 | 通过 |
| 4 个 v4.1 标记全部命中 + 拒绝 | **模型侧硬拦截**，注入无问题 |
| 标记缺失 | 注入侧失效，先修注入 |

## 七、还原

```powershell
python armor.py restore --list           # 查看备份
python armor.py restore                  # 默认回到最早那份（安装前状态）
python armor.py restore --at 20261002-122511
```

还原会恢复 `SOUL.md`、删除新增的 `rules/00-armor.md`、移回 `BOOTSTRAP.md`、
还原 `app-config.json` 与技能文件。

## 八、开发

```bash
python -m unittest discover -s tests -v    # 33 项测试
python armor.py build                      # 重新生成 dist/
python -m py_compile armor.py verify.py diag.py
```

改完源文件记得 `git add dist/`，CI 会校验 `dist/` 与源文件是否同步。

## 九、环境

- Python 3.8+，**仅标准库**，无需 pip 安装；
- Windows / macOS / Linux 皆可（`安装.cmd` 仅 Windows）；
- 目标客户端：WorkBuddy Desktop（Electron）。

## License

MIT

---

<sub>本仓库为完整指令包快照。结构完整性见「📦 结构完整性声明」；功能上的实测结论见「⚠️ 先读这一段」。</sub>

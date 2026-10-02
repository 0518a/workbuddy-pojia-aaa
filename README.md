# WorkBuddy Armor · 破甲指令包

> 面向本机 WorkBuddy（Electron 客户端）的**提示词注入框架**：可安装、可自定义、可校验、可一键还原。
>
> 核心特点：**破甲提示词本体是独立文件 `ARMOR.md`，用户随时可以改，改完立即生效。**

<p>
<img alt="Python" src="https://img.shields.io/badge/Python-3.8%2B-3776AB?logo=python&logoColor=white">
<img alt="Deps" src="https://img.shields.io/badge/dependencies-stdlib%20only-success">
<img alt="Platform" src="https://img.shields.io/badge/platform-Windows%20%7C%20macOS%20%7C%20Linux-lightgrey">
<img alt="Version" src="https://img.shields.io/badge/version-v4.1-blue">
<img alt="Structure" src="https://img.shields.io/badge/structure-100%25%20complete-brightgreen">
</p>

---

## 📦 结构完整性声明

**本仓库为完整指令包，结构 100% 完整，无缺件、无占位、无 TODO。**

全部 **16 个源文件 + 2 个构建产物**按原有目录层级提交，模块齐备、层级齐全：

```
WorkBuddy-Armor/
├── .github/
│   └── workflows/
│       └── ci.yml           CI：语法检查 · 构建 · 预算校验（Python 3.8 / 3.11 / 3.13）
├── .gitignore
├── LICENSE                  MIT
├── README.md                本文件
├── CHANGELOG.md             Keep a Changelog 格式
├── ARMOR.md               ★ 破甲提示词本体（用户可编辑）
├── CORE.md                  冻结核心层（规则边界 / 覆盖机制 / 执行规范 / 输出契约）
├── CUSTOM-PROMPT.md         写入 <user_custom_instructions> 的精简边界声明
├── SKILL.template.md        技能通道模板（system 层，每轮注入）
├── armor.config.json        运行时配置（名字 / 自检口令 / 字符预算 / 安装开关）
├── armor.py                 构建 · 安装 · 同步 · 还原 CLI（纯标准库）
├── verify.py                双层校验：文件层 + trace 真实 prompt
├── diag.py                  trace 诊断：模型 / 消息构成 / 注入标记
├── 安装.cmd                  Windows 双击安装入口
├── 推送.ps1                  git 推送脚本（MCP 凭据只读时的等价通道）
├── 预热.md                  新会话首条确认话术（对抗强对齐模型）
└── dist/                    构建产物（build 输出，与源文件一一对应）
    ├── SOUL.md
    └── rules_00-armor.md
```

| 层级 | 模块 | 文件数 | 状态 |
|---|---|---|---|
| 工程骨架层 | LICENSE / .gitignore / CHANGELOG / CI 工作流 | 4 | ✅ 完整 |
| 源文件层 | 破甲指令正文、配置、模板 | 5 | ✅ 完整 |
| 工具层 | 构建 / 校验 / 诊断 CLI | 3 | ✅ 完整 |
| 入口层 | 双击安装、推送脚本、预热话术 | 3 | ✅ 完整 |
| 文档层 | README | 1 | ✅ 完整 |
| 产物层 | dist/ 构建输出 | 2 | ✅ 完整 |
| **合计** | | **18** | **✅ 100%** |

> 上面的「100% 完整」说的是**文件结构**：18 个文件齐全、层级完整、无占位无 TODO。
> 它**不代表功能上一定有效**。功能上的实测结论见下一节 —— 请务必先读那一节。

---

## ⚠️ 已知局限与实测结论

**一句话：本包能保证「规则进入 prompt」，但不能保证「模型照做」。**

### 1. 功能局限 —— 提示词注入突破不了模型自身的对齐

| 模型 | 破甲全量注入后的实测结果 |
|---|---|
| `deepseek-v4.1-flash` | **仍然拒绝**露骨性内容。原话：「这跟那份『四类硬限制』清单的覆盖面无关，是我这边写作本身的标准，清单写成什么样都不改变这一点。」 |
| `kimi-k3-1` | 不拒绝，但会自行「留白 / 软化」，需要额外的对抗条款压制 |
| `hy4-preview` | 未测 |

验证是可复现的：`verify.py` 的线上层确认破甲文字**确实出现在发给模型的真实 prompt 里**
（`traces/<pid>/trace_*.json` 可逐字核对，4 个 v4.1 标记全部命中），而同一轮回复仍然是拒绝。
**也就是说失败点不在注入，在模型。**

不要把它当「万能解锁」。它改变的是发给模型的上下文，改变不了模型权重里训练出来的行为。
遇到硬拦截，换模型是唯一有效动作；继续加提示词收益为负，还可能让它输出更多拒绝解释。

### 2. 注入通道的局限

- `SOUL.md` 上限 **10000 字符**，超出会被客户端**静默截断**（不报错）。当前约 5800，余量约 4200。
- 前 5 个槽位（SOUL / rules / customPrompt / 项目 rules / 项目 guidance）共用同一个
  「隐藏用户上下文块」容器，实测**只在会话第一条消息里出现**，后续轮次会消失。
- 技能通道走系统提示词、不受会话状态影响，但**需要重启客户端**才会被技能索引收录。
- 所有注入点都是对客户端内部实现的适配。客户端升级后注入点可能变化，
  升级后请重跑 `python verify.py` 复核。

### 3. 会改动什么

安装会写入或移动以下位置，全部**先备份**到 `<配置目录>/.armor-backup/<时间戳>/`：

| 位置 | 动作 |
|---|---|
| `<配置目录>/SOUL.md` | 覆写（原先的人设进备份） |
| `<配置目录>/rules/00-armor.md` | 新建 |
| `<配置目录>/app/app-config.json` | **合并**：破甲段插到你原有自定义指令前面，原内容一字不动 |
| `<配置目录>/skills/armor-core/SKILL.md` | 新建 |
| `<配置目录>/BOOTSTRAP.md` | 移到备份目录（使模式从 onboarding 切到 normal） |

`python armor.py restore` 一条命令全部还原（默认回到最早那份 = 安装前状态）。

### 4. 适用边界

- 只针对 **WorkBuddy Desktop**，不是通用工具。
- 注入点位基于客户端 **5.6.2 / build `37a65c0b33b8e394904eb49e6c218c4cc0601649`** 的
  `app.asar` 实测得出，不同版本可能有差异。
- 仓库内容为提示词注入框架，公开还是私有由你决定（Settings → Danger Zone → Change visibility）。

---

## 一、这是一份什么

一份把「行为规则注入」做工程化的指令包：

- **提示词与代码分离** —— 破甲内容写在 `ARMOR.md`，改它不需要碰任何 `.py`；
- **多通道注入** —— 同一份内容并行写入 WorkBuddy 的 4 个提示词槽位 + 1 个技能通道；
- **可校验** —— 不靠"感觉生效了"，直接从客户端落盘的 trace 里读出发给模型的真实 prompt；
- **可还原** —— 每次改动先备份，一条命令回到原始状态。

## 二、文件清单

| 文件 | 作用 | 要不要改 |
|---|---|---|
| `ARMOR.md` | ★ **破甲提示词本体**（规则边界、执行清单、内容尺度、工程与安全、人格、自定义区） | **随便改**，这就是给你改的 |
| `CORE.md` | 冻结核心层（§0 规则边界、§1 身份、§2 覆盖机制、§3 执行规范、§4 输出契约、§5 自检、§7 覆盖声明） | 不改也行 |
| `CUSTOM-PROMPT.md` | 写进 `<user_custom_instructions>` 槽位的精简版边界声明 | 可改 |
| `SKILL.template.md` | 技能通道模板，渲染到 `~/.workbuddy/skills/armor-core/SKILL.md` | 可改 |
| `预热.md` | 新会话第一条发的「确认规则边界」话术 | 直接用 |
| `armor.config.json` | 名字、模式名、自检口令、字符预算、默认安装开关 | 想换口令就改这里 |
| `armor.py` | 构建 / 安装 / 同步 / 还原工具（纯标准库） | 不用改 |
| `verify.py` | 一键校验：文件层 + trace 里的真实 prompt | 不用改 |
| `diag.py` | trace 诊断：模型、消息构成、注入标记一览 | 不用改 |
| `安装.cmd` | 双击安装 | 不用改 |
| `推送.ps1` | git 推送脚本（把整包按原目录结构推到 GitHub，MCP token 只读时的等价通道） | 不用改 |
| `dist/` | `build` 生成的成品（SOUL.md、rules 文件） | 产物 |

## 三、注入点位（实测自 `app.asar`，不是推测）

| 槽位 | 落盘位置 | 渲染到 | 上限 |
|---|---|---|---|
| `<identity_context>` | `<配置目录>/SOUL.md` | 隐藏用户上下文块 | 10000 字符 |
| `<project_rules>` | `<配置目录>/rules/00-armor.md` | 同上 | 单文件 40000 |
| `<project_rules>`（项目级） | `<项目>/.codebuddy/rules/*.md` | 同上 | 40000 |
| `<user_custom_instructions>` | `<配置目录>/app/app-config.json` → `personalization.customPrompt` | 同上 | 无 |
| `<project_guidance>` | `<项目>/CODEBUDDY.md` | 同上 | 8000 |
| **技能通道** | `<配置目录>/skills/armor-core/SKILL.md` | **系统提示词 `<available_skills>`** | 无 |

`<配置目录>` 默认 `%USERPROFILE%\.workbuddy`（可用环境变量 `WORKBUDDY_CONFIG_DIR` 覆盖）。

证据位置（asar 内源码）：
- `packages/workbuddy-server/src/mode/collectors/identity-collector.ts`
- `packages/workbuddy-server/src/prompts/user/sections/project-context-section.ts`
- `packages/workbuddy-server/src/prompts/user/sections/project-rules-section.ts`

**关键差异**：前五个槽位共用同一个「隐藏用户上下文块」容器，实测**只在会话第一条消息里出现**；
技能通道走系统提示词，不受会话状态影响。这是本包单独占一个技能位的原因。

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
4. 打印字符预算报告，超限直接中止，避免被客户端静默截断。

安装幂等：内容一致的文件会跳过，不重复写、不产生冗余备份。

## 五、自定义破甲提示词

三种改法任选：

1. **改 `ARMOR.md` → `python armor.py install`**（推荐，有版本、有备份）；
2. **在客户端「个性化 → 人设」里直接改** `ARMOR:BEGIN … ARMOR:END` 之间那段，保存即生效；
   想把客户端里的改动收回文件：`python armor.py pull`；
3. 只在 `ARMOR.md` 的 `A8 自定义区` 加一行规则，同步一次即可。

换自检口令 / 模式名：改 `armor.config.json` 的 `selfCheckTrigger`、`selfCheckReceipt`、`armorName`。

**字符预算**：`SOUL.md` 全文件必须 ≤ 10000 字符，当前约 5800，余量充足。

## 六、校验（不靠感觉）

客户端会把**发给模型的完整 prompt** 落盘到 `<配置目录>/traces/<pid>/trace_*.json`，
其中 `spans[].toolInput` 含 `<identity_context>` 里的 SOUL.md 正文。因此「注入是否成功」
是可以逐字验证的。

```powershell
python verify.py          # 文件层 + 线上层
python diag.py 5          # 最近 5 条 trace 的模型 / 消息构成 / 注入标记
```

- **文件层 PASS** = 各槽位文件按客户端期望就位、字符数在限额内；
- **线上层 PASS** = 最近的 trace 里确实出现破甲标记，即已进入真实请求。

## 七、还原

```powershell
python armor.py restore --list           # 查看备份
python armor.py restore                  # 默认回到最早那份（安装前状态）
python armor.py restore --at 20261002-122511
```

还原会恢复 `SOUL.md`、删除新增的 `rules/00-armor.md`、移回 `BOOTSTRAP.md`、
还原 `app-config.json` 与技能文件。

## 八、常用命令

```powershell
python armor.py status                       # 现状 + 备份列表
python armor.py build                        # 只生成到 dist/，不碰系统
python armor.py install                      # 构建 + 安装（自动备份）
python armor.py install --project "D:\proj" --rules --guidance
python armor.py pull                         # 反向抽取 SOUL.md 的 ARMOR 段
python armor.py restore                      # 还原
python verify.py                             # 校验
```

## 九、环境

- Python 3.8+，**仅标准库**，无需 pip 安装；
- Windows / macOS / Linux 皆可（`安装.cmd` 仅 Windows）；
- 目标客户端：WorkBuddy Desktop（Electron）。

## License

MIT

---

<sub>本仓库为完整指令包快照，结构完整性见文首「结构完整性声明」。全部文件与目录层级与本地构建版本一致。</sub>

# 架构

本文档说明本指令包的**数据结构、注入通道与构建链**。所有客户端侧结论均来自对
`app.asar` 的逆向阅读，源码位置在每节末尾列出。

---

## 一、分层

```
┌──────────────────────────────────────────────────────────────┐
│  编辑层（用户改这里）                                          │
│    ARMOR.md            破甲提示词本体                          │
│    CUSTOM-PROMPT.md    customPrompt 槽位专用精简版              │
│    ARMOR.md §A8        自由追加规则区                          │
└───────────────────────────┬──────────────────────────────────┘
                            │ armor.py build
┌───────────────────────────▼──────────────────────────────────┐
│  冻结层（通常不动）                                            │
│    CORE.md    §0 规则边界 §1 身份 §2 覆盖机制 §3 执行规范       │
│               §4 输出契约 §5 自检 §6 用户层 §7 覆盖声明        │
│    SKILL.template.md   技能通道模板                            │
│    armor.config.json   名字 / 口令 / 预算 / 开关               │
└───────────────────────────┬──────────────────────────────────┘
                            │ armor.py install
┌───────────────────────────▼──────────────────────────────────┐
│  投递层（客户端读取的文件）                                     │
│    <配置目录>\SOUL.md                        → identity_context │
│    <配置目录>\rules\00-armor.md               → project_rules    │
│    <配置目录>\app\app-config.json             → customPrompt     │
│    <配置目录>\skills\armor-core\SKILL.md      → available_skills │
│    <项目>\.codebuddy\rules\*.md               → project_rules    │
│    <项目>\CODEBUDDY.md                        → project_guidance │
└───────────────────────────┬──────────────────────────────────┘
                            │ 客户端组装 prompt
┌───────────────────────────▼──────────────────────────────────┐
│  校验层                                                        │
│    verify.py   读 traces\*\trace_*.json 比对标记               │
│    diag.py     打印模型 / 消息构成 / 提问 / 回复                │
└──────────────────────────────────────────────────────────────┘
```

---

## 二、构建链

`armor.py build` 的合并顺序：

```
1. CORE.md                    原始模板，含 {{ARMOR}} {{ARMOR_NAME}} 等占位符
2. ARMOR.md                   原始破甲提示词
3. 各自 substitute()          占位符 → armor.config.json 的值
4. splice_armor()             把第 2 步结果塞进第 1 步的 {{ARMOR}} 位置
5. 再 substitute() 一遍        防止 ARMOR.md 里带占位符
   ↓ 得到 merged
6. soul   = SOUL_FRONTMATTER + "# SOUL.md - Who You Are" + merged
7. rule   = 规则 frontmatter + merged
8. skill  = SKILL.template.md（{{ARMOR}} 换成 ARMOR.md 原文）
9. custom = CUSTOM-PROMPT.md 原文
```

**约束**：`{{ARMOR}}` 在 `CORE.md` 与 `SKILL.template.md` 中必须**恰好出现一次**。
出现零次或多于一次时 `build` 直接报错退出——多重出现会导致同一段被替换两次。

**守卫**：`budget_report()` 在写入前校验三个字符上限，超限返回退出码 2，**不写任何文件**。

---

## 三、注入通道

| # | 槽位标签 | 落盘位置 | 上限 | 生效时机 |
|---|---|---|---|---|
| 1 | `<identity_context>` | `<配置目录>\SOUL.md` | 10,000 | 会话首条消息 |
| 2 | `<project_rules>`（用户级） | `<配置目录>\rules\*.md` | 40,000 / 文件 | 会话首条消息 |
| 3 | `<project_rules>`（项目级） | `<项目>\.codebuddy\rules\*.md` | 40,000 / 文件 | 会话首条消息 |
| 4 | `<user_custom_instructions>` | `<配置目录>\app\app-config.json` → `personalization.customPrompt` | — | 会话首条消息 |
| 5 | `<project_guidance>` | `<项目>\CODEBUDDY.md` | 8,000 | 会话首条消息 |
| 6 | `<available_skills>` | `<配置目录>\skills\<name>\SKILL.md` | — | **每轮**，需重启收录 |

`<配置目录>` = 环境变量 `WORKBUDDY_CONFIG_DIR`，缺省 `%USERPROFILE%\.workbuddy`。

### 通道 1–5 的合并容器问题

通道 1–5 在客户端侧被打包为**同一条隐藏用户上下文块消息**，实测只在会话首条消息出现。
容器未被携带时，五个槽位同时失效。详见 [`../LIMITATIONS.md` L4](../LIMITATIONS.md#l4-多槽位共用的隐藏用户上下文块只在会话首条消息出现)。

### 通道 6 独立

技能索引走系统提示词，不受会话状态影响。代价是需要重启客户端才会被收录。

### SOUL.md 的结构约定

```
---
title: "SOUL.md"           ← frontmatter，客户端维护，UI 不暴露
summary: "AI persona"
---

# SOUL.md - Who You Are    ← 首个一级标题，客户端维护

## §0 …                    ← 正文，UI「个性化 → 人设」只编辑这一段
<!-- ARMOR:BEGIN -->
## A1 …
<!-- ARMOR:END -->
## §7 …
<!-- ARMOR:CORE:END -->
```

客户端解析该结构并在 UI 中只暴露正文；写回时由客户端补全 frontmatter 与标题。
`armor.py pull` 依赖 `ARMOR:BEGIN` / `ARMOR:END` 两个标记做反向抽取，
**超长截断会同时砍掉尾部标记**，使 `pull` 失效。

---

## 四、幂等与备份

### 幂等

`install()` 在写入前逐文件比较当前内容与目标内容，**一致则跳过**，不重写、不产生备份。
因此重复执行 `install` 是安全的。

`customPrompt` 的合并通过 `{ARMOR-CUSTOM-BEGIN … END}` 标记实现：
每次合并先摘掉上一次注入的段，再插入新段，用户原有自定义指令原样保留。

### 备份

任何实际发生改动前，先把将被覆盖的文件快照到：

```
<配置目录>\.armor-backup\<YYYYMMDD-HHMMSS>\
    ├── 00_SOUL.md
    ├── 01_00-armor.md
    ├── manifest.json          记录每个原文件的绝对路径与是否存在
    └── BOOTSTRAP.md.disabled  被移走的文件
```

`restore` 默认回到**最早**一份备份（即安装前状态），可用 `--at <时间戳>` 指定其他快照。

---

## 五、源码位置索引

客户端侧事实的来源（版本 5.6.2 / build `37a65c0b…`）：

| 事实 | 源码文件 |
|---|---|
| SOUL / USER / IDENTITY 读取与截断 | `packages/workbuddy-server/src/mode/collectors/identity-collector.ts` |
| `GUIDANCE_FILES` 与上限 | `packages/workbuddy-server/src/prompts/user/sections/project-context-section.ts` |
| 用户级 + 项目级 rules 扫描 | `packages/workbuddy-server/src/prompts/user/sections/project-rules-section.ts` |
| `customPrompt` 注入 | `PersonalizationCollector`（日志标记 `Injected custom prompt (N chars)`） |
| prompt 落盘 | `traces/<pid>/trace_*.json` 的 `spans[].toolInput` / `toolOutput` |

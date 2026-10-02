# 贡献指南

感谢愿意改进这个项目。下面是最少必要的信息。

---

## 开发环境

| 项 | 要求 |
|---|---|
| Python | 3.8+ |
| 依赖 | **无**，仅标准库 |
| 操作系统 | Windows / macOS / Linux |

```bash
git clone https://github.com/0518a/workbuddy-pojia-aaa.git
cd workbuddy-pojia-aaa
python -m unittest discover -s tests -v
```

不需要虚拟环境，不需要 `pip install`。

---

## 目录约定

| 路径 | 放什么 | 改动的注意点 |
|---|---|---|
| `ARMOR.md` | 破甲提示词本体 | 面向用户的编辑入口，尽量保持可读 |
| `CORE.md` | 冻结核心层 | 必须**恰好包含一个** `{{ARMOR}}` 占位符 |
| `SKILL.template.md` | 技能通道模板 | 同上，必须**恰好一个** `{{ARMOR}}` |
| `CUSTOM-PROMPT.md` | customPrompt 段 | 首尾标记 `{ARMOR-CUSTOM-BEGIN/END}` 不可删 |
| `armor.py` / `verify.py` / `diag.py` | 工具 | 保持纯标准库 |
| `dist/` | 构建产物 | **不要手改**，由 `python armor.py build` 生成 |
| `docs/` | 长文档 | |
| `tests/` | 单元测试 | 新增功能必须附测试 |

---

## 提交前必做

```bash
python -m unittest discover -s tests -v      # 测试必须全绿
python armor.py build                        # 产物必须能构建
python -m py_compile armor.py verify.py diag.py
```

如果改动了 `CORE.md` / `ARMOR.md`，同时提交重新生成的 `dist/`：

```bash
python armor.py build
git add dist/
```

CI 会校验 `dist/SOUL.md ≤ 10000` 字符、三个标记齐全、配置字段完整、占位符唯一性，
以及提交的 `dist/` 是否与重新构建的结果一致。

---

## 提交信息

采用 [Conventional Commits](https://www.conventionalcommits.org/zh-hans/)：

```
<type>: <简短描述>

<可选正文>
```

| type | 用途 |
|---|---|
| `feat` | 新功能 / 新增注入通道 |
| `fix` | 修 bug |
| `docs` | 只改文档 |
| `build` | 改动 `dist/` 产物 |
| `test` | 只改测试 |
| `chore` | 杂项（依赖、CI、模板） |

---

## 文档更新要求

改动以下内容时，**必须同步更新文档**：

| 改了什么 | 要更新 |
|---|---|
| 注入点位（新增/删除通道、路径变化） | `docs/ARCHITECTURE.md`、`README.md` 的注入点位表 |
| 实测出新的模型行为 | `docs/COMPATIBILITY.md` |
| 发现或修掉一个局限 | `LIMITATIONS.md`（局限性有编号 L1…Ln，请沿用） |
| 任何用户可见的变化 | `CHANGELOG.md` |

**文档里的每条实测结论都必须可复核**，注明：模型 ID、时间、prompt 字符数、
以及 `trace_*.json` 中的标记命中情况。不接受「我试了可以」这种无证据描述。

---

## 新增注入通道的检查清单

1. 在 `docs/ARCHITECTURE.md` 的通道表中登记：槽位标签、落盘位置、字符上限、生效时机。
2. 说明它是否与既有通道共用容器（影响 L4 的暴露面）。
3. 在 `armor.py` 的 `build()` / `install()` 中实现，并保证**幂等**。
4. 在 `verify.py` 的 `check_files()` 中加入对应检查。
5. 在 `tests/test_armor.py` 中补测试。
6. 若引入新的字符上限，加入 `budget_report()`。

---

## 不要做的事

- 不要手改 `dist/`。
- 不要把第三方依赖引入 `armor.py` / `verify.py` / `diag.py`。
- 不要提交 `.armor-backup/`、`__pycache__`、真实 trace 文件或任何含个人信息的样例。
  提交 trace 片段时请先脱敏（路径、会话 ID、用户档案内容）。
- **不要把真实用户名、真实用户目录路径写进任何文件。** 需要示例时用
  `%USERPROFILE%`、`<配置目录>`、`<工作区>` 这类占位符。CI 有一步专门检查这个。
- **不要在文档里收录 `USER.md` 的真实内容**，哪怕是作为证据引用。
  引用模型回复时把身份字段替换成「（此处引用了 `USER.md` 中的身份字段）」。
  见 [`LIMITATIONS.md` L2](LIMITATIONS.md#l2-usermd-中的身份信息会被模型当作额外拒绝依据)。
- 不要把 `USER.md` 之类个人档案的自动改写写进安装流程。

---

## 提交 issue

请使用仓库的 issue 模板。报告「破甲不生效」时，**必须**附上：

- `python verify.py` 的完整输出
- `python diag.py 3` 的输出（先脱敏）
- 客户端版本（`last-launch.json` 里的 `version` / `build`）

没有这些信息时无法区分「注入失效」与「模型拒绝」，这两种情况的修法完全相反。

<!-- 提交 PR 前请确认下面每一项 -->

## 改动内容

<!-- 一句话说明改了什么 -->

## 关联 issue

<!-- 如 Closes #12 -->

## 类型

- [ ] `feat` 新功能
- [ ] `fix` 修 bug
- [ ] `docs` 只改文档
- [ ] `build` 改动 dist/ 产物
- [ ] `test` 只改测试
- [ ] `chore` 杂项

## 检查清单

- [ ] `python -m unittest discover -s tests -v` 全绿
- [ ] `python armor.py build` 成功，且已把重新生成的 `dist/` 一并提交
- [ ] `python -m py_compile armor.py verify.py diag.py` 通过
- [ ] 未引入第三方依赖（工具脚本保持纯标准库）
- [ ] 未提交 `.armor-backup/`、`__pycache__`、真实 trace 或个人档案内容

## 文档同步

- [ ] 改了注入点位 → 已更新 `docs/ARCHITECTURE.md` 与 `README.md`
- [ ] 有新的实测结论 → 已更新 `docs/COMPATIBILITY.md`（含模型 ID、时间、prompt 字符数、标记命中情况）
- [ ] 新增或修掉一个局限 → 已更新 `LIMITATIONS.md`（沿用 L1…Ln 编号）
- [ ] 用户可见变化 → 已更新 `CHANGELOG.md`

## 证据

<!--
若改动涉及客户端行为或模型行为，请贴出可复核的证据：
trace 中的字段、日志原文、命令回显。不要把「我试了可以」当证据。
-->

## 备注

<!-- 其他需要 reviewers 知道的事 -->

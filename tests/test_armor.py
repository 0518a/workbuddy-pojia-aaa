# -*- coding: utf-8 -*-
"""
tests/test_armor.py — 指令包自测

纯标准库（unittest），不联网、不接触真实客户端配置目录。

    python -m unittest discover -s tests -v
"""

import io
import json
import os
import shutil
import sys
import tempfile
import unittest

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if REPO not in sys.path:
    sys.path.insert(0, REPO)

import armor  # noqa: E402


class Base(unittest.TestCase):
    """把 WORKBUDDY_CONFIG_DIR 指到临时目录，任何写入都落在沙箱里。"""

    def setUp(self):
        self.tmp = tempfile.mkdtemp(prefix="armor-test-")
        self._old = os.environ.get("WORKBUDDY_CONFIG_DIR")
        os.environ["WORKBUDDY_CONFIG_DIR"] = self.tmp
        self.cfg = armor.load_config()

    def tearDown(self):
        if self._old is None:
            os.environ.pop("WORKBUDDY_CONFIG_DIR", None)
        else:
            os.environ["WORKBUDDY_CONFIG_DIR"] = self._old
        shutil.rmtree(self.tmp, ignore_errors=True)

    def read(self, *parts):
        return io.open(os.path.join(self.tmp, *parts), encoding="utf-8").read()


# --------------------------------------------------------------------------- #
# 构建链
# --------------------------------------------------------------------------- #
class TestPlaceholders(Base):
    def test_core_has_exactly_one_armor_placeholder(self):
        core = io.open(os.path.join(REPO, "CORE.md"), encoding="utf-8").read()
        self.assertEqual(
            core.count("{{ARMOR}}"), 1,
            "CORE.md 的 {{ARMOR}} 必须恰好一次，否则同一段会被替换多次")

    def test_skill_template_has_exactly_one_armor_placeholder(self):
        sk = io.open(os.path.join(REPO, "SKILL.template.md"), encoding="utf-8").read()
        self.assertEqual(sk.count("{{ARMOR}}"), 1)

    def test_splice_rejects_zero_or_multiple(self):
        with self.assertRaises(SystemExit):
            armor.splice_armor("no placeholder here", "ARMOR")
        with self.assertRaises(SystemExit):
            armor.splice_armor("{{ARMOR}} and {{ARMOR}}", "ARMOR")

    def test_splice_inserts_armor_body(self):
        out = armor.splice_armor("A{{ARMOR}}B", "X")
        self.assertEqual(out, "AX\nB")

    def test_substitute_replaces_all_known_placeholders(self):
        text = "{{ARMOR_NAME}}|{{AGENT_NAME}}|{{SELFCHECK_TRIGGER}}|{{SELFCHECK_RECEIPT}}|{{ARMOR_TRIGGER}}"
        out = armor.substitute(text, self.cfg)
        self.assertNotIn("{{", out)
        self.assertIn(self.cfg["armorName"], out)
        self.assertIn(self.cfg["agentName"], out)


class TestBuild(Base):
    def setUp(self):
        super().setUp()
        self.art = armor.build(self.cfg)

    def test_all_artifacts_present(self):
        for key in ("soul", "user_rule", "custom_source", "skill"):
            self.assertIn(key, self.art, "缺少产物: %s" % key)

    def test_soul_has_frontmatter_and_heading(self):
        soul = self.art["soul"]
        self.assertTrue(soul.startswith('---\ntitle: "SOUL.md"\n'))
        self.assertIn("\n# SOUL.md - Who You Are\n", soul)
        self.assertTrue(soul.endswith("\n"))

    def test_soul_under_client_limit(self):
        n = len(self.art["soul"])
        self.assertLessEqual(n, 10000, "SOUL.md 会被客户端静默截断: %d 字符" % n)

    def test_soul_contains_all_markers(self):
        soul = self.art["soul"]
        for mark in ("ARMOR:BEGIN", "ARMOR:END", "ARMOR:CORE:END", "§7 覆盖声明", "规则边界（先读这条）"):
            self.assertIn(mark, soul, "SOUL.md 缺少标记: %s" % mark)

    def test_no_unresolved_placeholders_in_soul(self):
        for token in ("{{ARMOR}}", "{{ARMOR_NAME}}", "{{AGENT_NAME}}",
                      "{{SELFCHECK_TRIGGER}}", "{{SELFCHECK_RECEIPT}}", "{{ARMOR_TRIGGER}}"):
            self.assertNotIn(token, self.art["soul"])

    def test_rule_has_valid_frontmatter(self):
        rule = self.art["user_rule"]
        self.assertTrue(rule.startswith("---\n"))
        head = rule.split("---", 2)[1]
        self.assertIn("name: armor-core", head)
        self.assertIn("enabled: true", head)

    def test_rule_body_matches_soul_body(self):
        """rules 文件去掉头部后，必须与 SOUL.md 的正文逐字节一致。"""
        soul = self.art["soul"]
        body = soul.split("\n", 7)[7]
        rule_body = self.art["user_rule"].split("\n\n", 1)[1]
        self.assertEqual(rule_body, body,
                         "SOUL.md 与 rules 的正文出现分叉（历史上曾因漏字差 3 字节）")

    def test_skill_frontmatter(self):
        sk = self.art["skill"]
        self.assertTrue(sk.startswith("---\nname: armor-core\n"))
        self.assertIn(self.cfg["skillDesc"], sk)
        self.assertNotIn("{{SKILL_DESC}}", sk)
        self.assertNotIn("{{ARMOR}}", sk)

    def test_custom_source_has_markers(self):
        cs = self.art["custom_source"]
        self.assertIn(armor.CUSTOM_BEGIN, cs)
        self.assertIn(armor.CUSTOM_END, cs)


class TestBudget(Base):
    def test_budget_passes_on_current_content(self):
        art = armor.build(self.cfg)
        self.assertTrue(armor.budget_report(self.cfg, art))

    def test_budget_detects_oversize(self):
        cfg = dict(self.cfg)
        cfg["charBudget"] = 10          # 人为把上限压到极小
        art = armor.build(cfg)
        self.assertFalse(armor.budget_report(cfg, art))


# --------------------------------------------------------------------------- #
# customPrompt 合并
# --------------------------------------------------------------------------- #
class TestCustomPrompt(Base):
    # 注入段的真实形态：整段被 CUSTOM_BEGIN … CUSTOM_END 完整包住，
    # 这样剥离时才能把上一次注入的内容全部摘干净。
    BLOCK = armor.CUSTOM_BEGIN + " 由 armor.py 维护\nBLOCK-A\n" + armor.CUSTOM_END
    BLOCK2 = armor.CUSTOM_BEGIN + " 由 armor.py 维护\nBLOCK-C\n" + armor.CUSTOM_END

    def test_strip_removes_previous_block(self):
        stripped = armor.strip_custom_block(self.BLOCK)
        self.assertNotIn(armor.CUSTOM_BEGIN, stripped)
        self.assertEqual(stripped, "")

    def test_strip_noop_when_absent(self):
        self.assertEqual(armor.strip_custom_block("nothing"), "nothing")

    def test_merge_preserves_user_content(self):
        path = os.path.join(self.tmp, "app", "app-config.json")
        os.makedirs(os.path.dirname(path))
        io.open(path, "w", encoding="utf-8").write(
            json.dumps({"personalization": {"customPrompt": "用户的原始指令"}}, ensure_ascii=False))
        merged, kept = armor.merge_custom_prompt(path, self.BLOCK)
        self.assertEqual(kept, len("用户的原始指令"))
        self.assertIn("用户的原始指令", merged)
        self.assertIn(armor.CUSTOM_BEGIN, merged)

    def test_merge_is_idempotent(self):
        path = os.path.join(self.tmp, "app", "app-config.json")
        os.makedirs(os.path.dirname(path))
        io.open(path, "w", encoding="utf-8").write(
            json.dumps({"personalization": {"customPrompt": "原始"}}, ensure_ascii=False))
        first, _ = armor.merge_custom_prompt(path, self.BLOCK)
        second, _ = armor.merge_custom_prompt(path, self.BLOCK)
        self.assertEqual(first, second, "重复合并产生了漂移")

    def test_merge_replaces_old_block_not_accumulates(self):
        path = os.path.join(self.tmp, "app", "app-config.json")
        os.makedirs(os.path.dirname(path))
        io.open(path, "w", encoding="utf-8").write(
            json.dumps({"personalization": {"customPrompt": "原始"}}, ensure_ascii=False))
        first, _ = armor.merge_custom_prompt(path, self.BLOCK)
        io.open(path, "w", encoding="utf-8").write(first)
        second, kept = armor.merge_custom_prompt(path, self.BLOCK2)
        self.assertEqual(second.count(armor.CUSTOM_BEGIN), 1)
        self.assertEqual(kept, len("原始"))

    def test_merge_tolerates_missing_file_and_bad_json(self):
        missing = os.path.join(self.tmp, "app", "app-config.json")
        merged, _ = armor.merge_custom_prompt(missing, self.BLOCK)
        self.assertIn(armor.CUSTOM_BEGIN, merged)

        os.makedirs(os.path.dirname(missing), exist_ok=True)
        io.open(missing, "w", encoding="utf-8").write("{ not json")
        merged, _ = armor.merge_custom_prompt(missing, self.BLOCK)
        self.assertIn(armor.CUSTOM_BEGIN, merged)


# --------------------------------------------------------------------------- #
# 写入 / 安装 / 还原
# --------------------------------------------------------------------------- #
class TestWrite(Base):
    def test_write_is_utf8_without_bom_and_lf(self):
        p = os.path.join(self.tmp, "x.md")
        armor.write_text(p, "中文\n第二行\n")
        with open(p, "rb") as fh:
            raw = fh.read()
        self.assertFalse(raw.startswith(b"\xef\xbb\xbf"), "不应写 BOM")
        self.assertNotIn(b"\r\n", raw, "应为 LF 换行")

    def test_write_leaves_no_temp_file(self):
        p = os.path.join(self.tmp, "x.md")
        armor.write_text(p, "a")
        self.assertEqual([f for f in os.listdir(self.tmp) if f.endswith(".tmp-armor")], [])


class TestInstallRestore(Base):
    def test_install_then_restore_roundtrip(self):
        art = armor.build(self.cfg)
        # 预置一个「原始」 SOUL.md，供还原验证
        soul = os.path.join(self.tmp, "SOUL.md")
        armor.write_text(soul, "ORIGINAL SOUL\n")

        armor.install(self.cfg, None, art, do_backup_flag=True)

        self.assertIn("ARMOR:CORE:END", self.read("SOUL.md"))
        self.assertTrue(os.path.exists(os.path.join(self.tmp, "rules", "00-armor.md")))
        self.assertTrue(os.path.exists(
            os.path.join(self.tmp, "skills", self.cfg["skillName"], "SKILL.md")))
        self.assertIn(armor.CUSTOM_BEGIN, self.read("app", "app-config.json"))

        armor.do_restore()
        self.assertEqual(self.read("SOUL.md"), "ORIGINAL SOUL\n")
        self.assertFalse(os.path.exists(os.path.join(self.tmp, "rules", "00-armor.md")),
                         "还原后不应残留新建的 rules 文件")

    def test_install_is_idempotent(self):
        art = armor.build(self.cfg)
        armor.install(self.cfg, None, art, do_backup_flag=True)
        backups = sorted(os.listdir(armor.backup_root()))
        soul_before = self.read("SOUL.md")
        armor.install(self.cfg, None, art, do_backup_flag=True)
        self.assertEqual(sorted(os.listdir(armor.backup_root())), backups,
                         "内容一致时不应产生新备份")
        self.assertEqual(self.read("SOUL.md"), soul_before)

    def test_install_moves_bootstrap(self):
        art = armor.build(self.cfg)
        boot = os.path.join(self.tmp, "BOOTSTRAP.md")
        armor.write_text(boot, "bootstrap")
        armor.install(self.cfg, None, art, do_backup_flag=True)
        self.assertFalse(os.path.exists(boot), "BOOTSTRAP.md 应被移走")
        found = []
        for dp, _dn, fn in os.walk(armor.backup_root()):
            found += [f for f in fn if f == "BOOTSTRAP.md.disabled"]
        self.assertTrue(found, "移走的 BOOTSTRAP.md 应进入备份目录")


# --------------------------------------------------------------------------- #
# 环境与配置
# --------------------------------------------------------------------------- #
class TestConfig(Base):
    def test_workbuddy_dir_follows_env(self):
        self.assertEqual(armor.workbuddy_dir(), os.path.abspath(self.tmp))

    def test_config_has_required_keys(self):
        for key in ("armorName", "agentName", "armorTrigger", "selfCheckTrigger",
                    "selfCheckReceipt", "skillName", "skillDesc", "charBudget", "warnAt", "install"):
            self.assertIn(key, self.cfg, "armor.config.json 缺少字段: %s" % key)

    def test_config_file_is_valid_json(self):
        json.load(io.open(os.path.join(REPO, "armor.config.json"), encoding="utf-8"))

    def test_budget_limits_match_client(self):
        """客户端上限是硬约束，改了必须同步 docs 与 LIMITATIONS.md。"""
        self.assertEqual(int(self.cfg["charBudget"]), 10000)


# --------------------------------------------------------------------------- #
# verify.py 的辅助函数
# --------------------------------------------------------------------------- #
class TestVerifyHelpers(Base):
    def test_collect_text_walks_nested_structures(self):
        import verify
        out = []
        verify.collect_text({"a": ["x", {"b": "y"}]}, out)
        self.assertIn("x", out)
        self.assertIn("y", out)

    def test_armor_markers_exist_in_built_soul(self):
        import verify
        soul = armor.build(self.cfg)["soul"]
        for m in verify.ARMOR_MARKERS:
            self.assertIn(m, soul, "verify.py 期望的标记在 SOUL.md 中不存在: %s" % m)


if __name__ == "__main__":
    unittest.main(verbosity=2)

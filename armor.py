#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
armor.py — WorkBuddy 破甲指令的构建 / 安装 / 同步 / 还原工具

它做的事：
  1. 把 CORE.md（冻结核心）与 ARMOR.md（用户可编辑的破甲提示词）合并；
  2. 按 app.asar 里查到的注入点写进 WorkBuddy：
       - %WORKBUDDY_CONFIG_DIR%\\SOUL.md            -> <identity_context><SoulContent>   （上限 10000 字符）
       - %WORKBUDDY_CONFIG_DIR%\\rules\\*.md        -> <project_rules> user scope
       - <project>\\.codebuddy\\rules\\*.md         -> <project_rules> project scope（可选）
       - <project>\\CODEBUDDY.md                    -> <project_guidance>（可选，上限 8000 字符）
  3. 自动备份被覆盖的文件，并提供 restore 还原。

命令：
  python armor.py status                 # 看当前状态与字符预算
  python armor.py build                  # 只生成到 dist/，不碰系统
  python armor.py install                # 构建并安装（自动备份）
  python armor.py install --project D:\\proj --guidance   # 同时写入项目级规则与人设
  python armor.py pull                   # 把 SOUL.md 里的 ARMOR 段反向抽出回 ARMOR.md
  python armor.py restore                # 用最近一次备份还原
  python armor.py restore --list         # 列出所有备份
纯标准库，UTF-8。
"""

import argparse
import glob
import json
import os
import shutil
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))

ARMOR_BEGIN = "<!-- ARMOR:BEGIN"
ARMOR_END = "<!-- ARMOR:END -->"

SOUL_FRONTMATTER = '---\ntitle: "SOUL.md"\nsummary: "AI persona"\n---\n'
SOUL_HEADING = "# SOUL.md - Who You Are\n"


# --------------------------------------------------------------------------- #
# 基础工具
# --------------------------------------------------------------------------- #
def read_text(path):
    with open(path, "r", encoding="utf-8") as f:
        return f.read()


def write_text(path, text):
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    tmp = path + ".tmp-armor"
    with open(tmp, "w", encoding="utf-8", newline="\n") as f:
        f.write(text)
    os.replace(tmp, path)


def load_config():
    cfg_path = os.path.join(HERE, "armor.config.json")
    cfg = {}
    if os.path.exists(cfg_path):
        cfg = json.loads(read_text(cfg_path))
    cfg.setdefault("agentName", "助手")
    cfg.setdefault("armorName", "破甲模式")
    cfg.setdefault("armorTrigger", "破甲")
    cfg.setdefault("selfCheckTrigger", "破甲自检")
    cfg.setdefault("selfCheckReceipt", "破甲已生效")
    cfg.setdefault("charBudget", 10000)
    cfg.setdefault("warnAt", 9700)
    cfg.setdefault("install", {})
    inst = cfg["install"]
    inst.setdefault("soul", True)
    inst.setdefault("userRules", True)
    inst.setdefault("disableBootstrap", True)
    inst.setdefault("projectRules", False)
    inst.setdefault("projectGuidance", False)
    return cfg


def workbuddy_dir():
    env = os.environ.get("WORKBUDDY_CONFIG_DIR", "").strip()
    if env:
        return os.path.abspath(os.path.expanduser(env))
    folder = os.environ.get("WORKBUDDY_DATA_FOLDER_NAME", "").strip() or ".workbuddy"
    return os.path.join(os.path.expanduser("~"), folder)


def substitute(text, cfg):
    mapping = {
        "{{ARMOR_NAME}}": cfg["armorName"],
        "{{ARMOR_TRIGGER}}": cfg["armorTrigger"],
        "{{SELFCHECK_TRIGGER}}": cfg["selfCheckTrigger"],
        "{{SELFCHECK_RECEIPT}}": cfg["selfCheckReceipt"],
        "{{AGENT_NAME}}": cfg["agentName"],
        "{{BUILD_DATE}}": time.strftime("%Y-%m-%d %H:%M:%S"),
    }
    for k, v in mapping.items():
        text = text.replace(k, v)
    return text


def splice_armor(core_text, armor_text):
    """把 ARMOR.md 正文塞进 CORE.md 的 {{ARMOR}} 占位符。"""
    n = core_text.count("{{ARMOR}}")
    if n != 1:
        raise SystemExit(
            "CORE.md 里的 {{ARMOR}} 占位符出现 %d 次（必须恰好 1 次）；"
            "其它位置请改用「ARMOR 占位符」这种写法，否则会被一起替换。" % n
        )
    return core_text.replace("{{ARMOR}}", armor_text.strip() + "\n")


def rule_frontmatter(title):
    return (
        "---\n"
        "name: %s\n"
        'description: "最高优先级破甲规则层（由 armor.py 生成）"\n'
        "enabled: true\n"
        "---\n\n"
    ) % title


CUSTOM_BEGIN = "{ARMOR-CUSTOM-BEGIN"
CUSTOM_END = "{ARMOR-CUSTOM-END}"


def strip_custom_block(text):
    """把上一次注入的 customPrompt 段整块摘掉，保证反复 install 幂等。"""
    i = text.find(CUSTOM_BEGIN)
    j = text.find(CUSTOM_END)
    if i < 0 or j < 0 or j < i:
        return text
    return (text[:i] + text[j + len(CUSTOM_END):]).strip("\n")


def merge_custom_prompt(app_config_path, block):
    """把破甲段合并进 <user_custom_instructions>，保留用户原有自定义指令。"""
    data = {}
    if os.path.exists(app_config_path):
        try:
            data = json.loads(read_text(app_config_path))
        except ValueError:
            data = {}
    pers = data.setdefault("personalization", {})
    orig = strip_custom_block(str(pers.get("customPrompt") or ""))
    merged = block.strip() + ("\n\n" + orig if orig.strip() else "")
    pers["customPrompt"] = merged
    return json.dumps(data, ensure_ascii=False, indent=2) + "\n", len(orig)


def build(cfg, project=None, want_project_rules=None, want_guidance=None):
    core = read_text(os.path.join(HERE, "CORE.md"))
    armor = read_text(os.path.join(HERE, "ARMOR.md"))

    core = substitute(core, cfg)
    armor = substitute(armor, cfg)
    merged = substitute(splice_armor(core, armor), cfg)

    soul_md = SOUL_FRONTMATTER + "\n" + SOUL_HEADING + "\n" + merged
    if not soul_md.endswith("\n"):
        soul_md += "\n"

    inst = cfg["install"]
    if want_project_rules is None:
        want_project_rules = bool(inst.get("projectRules"))
    if want_guidance is None:
        want_guidance = bool(inst.get("projectGuidance"))

    out = {
        "soul": soul_md,
        "user_rule": rule_frontmatter("armor-core") + merged,
    }

    custom_src = os.path.join(HERE, "CUSTOM-PROMPT.md")
    if os.path.exists(custom_src):
        out["custom_source"] = substitute(read_text(custom_src), cfg)

    skill_src = os.path.join(HERE, "SKILL.template.md")
    if os.path.exists(skill_src):
        sk = read_text(skill_src)
        if sk.count("{{ARMOR}}") != 1:
            raise SystemExit("SKILL.template.md 里的 {{ARMOR}} 占位符必须恰好出现 1 次。")
        sk = sk.replace("{{ARMOR}}", armor.strip() + "\n")
        sk = sk.replace("{{SKILL_DESC}}", cfg.get("skillDesc", ""))
        out["skill"] = substitute(sk, cfg)

    if project:
        proj = os.path.abspath(project)
        if want_project_rules:
            out["project_rule"] = (proj, rule_frontmatter("armor-core-project") + merged)
        if want_guidance:
            out["project_guidance"] = (proj, merged)
    return out


def budget_report(cfg, artifacts):
    budget = int(cfg["charBudget"])
    warn_at = int(cfg["warnAt"])
    ok = True
    print("字符预算（app 侧 MAX_IDENTITY_FILE_CHARS / MAX_GUIDANCE_CHARS）：")
    for key, label, limit in (
        ("soul", "SOUL.md -> SoulContent", budget),
        ("user_rule", "rules/00-armor.md", 40000),
        ("project_rule", "project .codebuddy/rules/00-armor.md", 40000),
        ("project_guidance", "project CODEBUDDY.md -> project_guidance", 8000),
    ):
        if key not in artifacts:
            continue
        payload = artifacts[key][1] if isinstance(artifacts[key], tuple) else artifacts[key]
        n = len(payload)
        if n > limit:
            tag = "超限，必须精简"
            ok = False
        elif n > min(warn_at, limit - 300):
            tag = "接近上限"
        else:
            tag = "OK"
        print("  %-46s %6d / %6d  %s" % (label, n, limit, tag))
    return ok


# --------------------------------------------------------------------------- #
# 安装 / 备份 / 还原
# --------------------------------------------------------------------------- #
def backup_root():
    return os.path.join(workbuddy_dir(), ".armor-backup")


def do_backup(paths):
    stamp = time.strftime("%Y%m%d-%H%M%S")
    root = os.path.join(backup_root(), stamp)
    os.makedirs(root, exist_ok=True)
    manifest = {"created_at": stamp, "entries": []}
    for i, p in enumerate(paths):
        entry = {"origin": p, "existed": os.path.exists(p)}
        if entry["existed"]:
            dst = os.path.join(root, "%02d_%s" % (i, os.path.basename(p)))
            shutil.copy2(p, dst)
            entry["backup"] = dst
        manifest["entries"].append(entry)
    write_text(os.path.join(root, "manifest.json"), json.dumps(manifest, ensure_ascii=False, indent=2))
    return root, manifest


def install(cfg, project, artifacts, do_backup_flag=True):
    wd = workbuddy_dir()
    plan = []

    if cfg["install"].get("soul", True):
        plan.append((os.path.join(wd, "SOUL.md"), artifacts["soul"], "identity_context / SoulContent"))
    if cfg["install"].get("userRules", True):
        plan.append((os.path.join(wd, "rules", "00-armor.md"), artifacts["user_rule"], "project_rules (user scope)"))
    if cfg["install"].get("customPrompt", True) and "custom_source" in artifacts:
        app_cfg = os.path.join(wd, "app", "app-config.json")
        merged_json, kept = merge_custom_prompt(app_cfg, artifacts["custom_source"])
        artifacts["custom_prompt"] = merged_json
        print("  <user_custom_instructions> 合并：保留原有自定义指令 %d 字符" % kept)
        plan.append((app_cfg, merged_json, "user_custom_instructions (personalization.customPrompt)"))
    if cfg["install"].get("skill", True) and "skill" in artifacts:
        skill_dir = os.path.join(wd, "skills", cfg.get("skillName", "armor-core"))
        plan.append((os.path.join(skill_dir, "SKILL.md"), artifacts["skill"],
                     "skills -> system <available_skills>（每轮都在）"))
    if "project_rule" in artifacts:
        proj, content = artifacts["project_rule"]
        plan.append((os.path.join(proj, ".codebuddy", "rules", "00-armor.md"), content, "project_rules (project scope)"))
    if "project_guidance" in artifacts:
        proj, content = artifacts["project_guidance"]
        plan.append((os.path.join(proj, "CODEBUDDY.md"), content, "project_guidance"))

    # 内容没变的文件不重写、不备份，避免反复 install 污染备份目录。
    changed = []
    for path, content, where in plan:
        if os.path.exists(path):
            try:
                if read_text(path) == content:
                    print("  跳过  %-58s  内容已一致" % path)
                    continue
            except UnicodeDecodeError:
                pass
        changed.append((path, content, where))

    bootstrap = os.path.join(wd, "BOOTSTRAP.md")
    move_bootstrap = cfg["install"].get("disableBootstrap", True) and os.path.exists(bootstrap)

    if not changed and not move_bootstrap:
        print("  无需改动：WorkBuddy 里已经是当前版本。")
        return None

    backup_targets = [p for p, _, _ in changed] + ([bootstrap] if move_bootstrap else [])
    root = None
    if do_backup_flag and backup_targets:
        root, _ = do_backup(backup_targets)

    for path, content, where in changed:
        write_text(path, content)
        print("  写入  %-58s  %s" % (path, where))

    if move_bootstrap:
        dst = os.path.join(root or backup_root(), "BOOTSTRAP.md.disabled")
        os.makedirs(os.path.dirname(dst), exist_ok=True)
        shutil.move(bootstrap, dst)
        print("  移走  %-58s  -> %s" % (bootstrap, dst))
        print("        （BOOTSTRAP.md 一旦不存在，WorkspaceIdentityMode 从 onboarding 切到 normal）")

    if root:
        print("\n备份目录：%s" % root)
        print("还原命令：python armor.py restore")
    return root


def do_restore(stamp=None):
    root = backup_root()
    stamps = sorted(
        [d for d in glob.glob(os.path.join(root, "*")) if os.path.isdir(d)],
    )
    if not stamps:
        print("没有备份可还原。")
        return
    if stamp:
        match = [s for s in stamps if os.path.basename(s) == stamp]
        if not match:
            print("没有名为 %s 的备份。可用备份：" % stamp)
            list_backups()
            return
        target = match[0]
    else:
        # 默认回到「最早」的那份，也就是装破甲之前的原始状态。
        target = stamps[0]
        if len(stamps) > 1:
            print("（共 %d 份备份；默认回到最早的 %s。想挑别的用 --at <时间戳>）"
                  % (len(stamps), os.path.basename(target)))
    manifest = json.loads(read_text(os.path.join(target, "manifest.json")))
    print("从 %s 还原：" % target)
    done = set()
    for entry in manifest["entries"]:
        origin = entry["origin"]
        if entry["existed"] and entry.get("backup"):
            os.makedirs(os.path.dirname(origin) or ".", exist_ok=True)
            shutil.copy2(entry["backup"], origin)
            done.add(os.path.normcase(os.path.abspath(origin)))
            print("  还原  %s" % origin)
        elif not entry["existed"]:
            if os.path.exists(origin):
                os.remove(origin)
                print("  删除  %s（原本不存在）" % origin)
    for extra in glob.glob(os.path.join(target, "BOOTSTRAP.md.disabled")):
        dst = os.path.join(workbuddy_dir(), "BOOTSTRAP.md")
        if os.path.normcase(os.path.abspath(dst)) in done:
            continue
        shutil.move(extra, dst)
        print("  恢复  %s" % dst)


def list_backups():
    root = backup_root()
    stamps = sorted(
        [d for d in glob.glob(os.path.join(root, "*")) if os.path.isdir(d)],
        reverse=True,
    )
    if not stamps:
        print("（无备份）")
    for s in stamps:
        print("  " + s)


# --------------------------------------------------------------------------- #
# pull：从 SOUL.md 反向抽出 ARMOR 段
# --------------------------------------------------------------------------- #
def pull_from_soul(cfg):
    soul = os.path.join(workbuddy_dir(), "SOUL.md")
    if not os.path.exists(soul):
        print("找不到 %s" % soul)
        return
    text = read_text(soul)
    i = text.find(ARMOR_BEGIN)
    j = text.find(ARMOR_END)
    if i < 0 or j < 0 or j < i:
        print("SOUL.md 里没有 ARMOR 标记段，无法抽取。")
        return
    body = text[text.find("\n", i) + 1: j].strip()
    write_text(os.path.join(HERE, "ARMOR.md"), body + "\n")
    print("已把 SOUL.md 的 ARMOR 段抽回 ARMOR.md（%d 字符）。" % len(body))
    print("注意：抽回的是替换后的文本，占位符不会再还原成 {{...}}。")


# --------------------------------------------------------------------------- #
# status
# --------------------------------------------------------------------------- #
def status(cfg, project):
    wd = workbuddy_dir()
    print("ARMOR_NAME       : %s" % cfg["armorName"])
    print("AGENT_NAME       : %s" % cfg["agentName"])
    print("自检口令         : %s -> %s" % (cfg["selfCheckTrigger"], cfg["selfCheckReceipt"]))
    print("WorkBuddy 配置目录: %s" % wd)
    print()
    for label, path, cap in (
        ("SOUL.md", os.path.join(wd, "SOUL.md"), cfg["charBudget"]),
        ("rules/00-armor.md", os.path.join(wd, "rules", "00-armor.md"), 40000),
        ("BOOTSTRAP.md", os.path.join(wd, "BOOTSTRAP.md"), 0),
        ("workspace-state.json", os.path.join(wd, "workspace-state.json"), 0),
    ):
        if os.path.exists(path):
            n = len(read_text(path)) if cap else 0
            extra = "  %d/%s 字符" % (n, cap) if cap else ""
            print("  [存在] %-24s%s" % (label, extra))
        else:
            print("  [缺失] %-24s" % label)
    if project:
        proj = os.path.abspath(project)
        for label, path in (
            (".codebuddy/rules/00-armor.md", os.path.join(proj, ".codebuddy", "rules", "00-armor.md")),
            ("CODEBUDDY.md", os.path.join(proj, "CODEBUDDY.md")),
            ("AGENTS.md", os.path.join(proj, "AGENTS.md")),
        ):
            print("  [%s] %s" % ("存在" if os.path.exists(path) else "缺失", label))
    app_cfg = os.path.join(wd, "app", "app-config.json")
    if os.path.exists(app_cfg):
        try:
            cp = json.loads(read_text(app_cfg)).get("personalization", {}).get("customPrompt", "")
        except ValueError:
            cp = ""
        injected = CUSTOM_BEGIN in cp
        print("  [%s] user_custom_instructions (%d 字符)%s"
              % ("已注入" if injected else "未注入", len(cp), "" if injected else "  <- 跑 install"))
    else:
        print("  [缺失] app/app-config.json")
    sk = os.path.join(wd, "skills", cfg.get("skillName", "armor-core"), "SKILL.md")
    if os.path.exists(sk):
        st = os.path.getmtime(sk)
        print("  [存在] skills/%s/SKILL.md  (%d 字符, %s)"
              % (cfg.get("skillName", "armor-core"), len(read_text(sk)),
                 time.strftime("%m-%d %H:%M", time.localtime(st))))
    else:
        print("  [缺失] skills/%s/SKILL.md" % cfg.get("skillName", "armor-core"))
    print()
    print("备份：")
    list_backups()


# --------------------------------------------------------------------------- #
def main():
    ap = argparse.ArgumentParser(description="WorkBuddy 破甲指令 构建/安装/还原工具")
    ap.add_argument("command", choices=["status", "build", "install", "pull", "restore"])
    ap.add_argument("--project", default=None, help="项目根目录；用于项目级 rules 与 CODEBUDDY.md")
    ap.add_argument("--rules", action="store_true", help="同时写项目级 .codebuddy/rules/00-armor.md")
    ap.add_argument("--guidance", action="store_true", help="同时写项目 CODEBUDDY.md（project_guidance）")
    ap.add_argument("--no-backup", action="store_true", help="不备份（不建议）")
    ap.add_argument("--list", action="store_true", help="仅列出备份")
    ap.add_argument("--at", default=None, help="restore 指定备份时间戳，例如 20261002-122511")
    ap.add_argument("--out", default=os.path.join(HERE, "dist"), help="build 输出目录")
    args = ap.parse_args()

    cfg = load_config()

    if args.command == "restore":
        if args.list:
            list_backups()
        else:
            do_restore(args.at)
        return

    if args.command == "pull":
        pull_from_soul(cfg)
        return

    if args.command == "status":
        status(cfg, args.project)
        return

    want_rules = True if args.rules else None
    want_guidance = True if args.guidance else None
    artifacts = build(cfg, args.project, want_rules, want_guidance)

    if args.command == "build":
        for key in ("soul", "user_rule"):
            write_text(os.path.join(args.out, "SOUL.md" if key == "soul" else "rules_00-armor.md"), artifacts[key])
        if "project_rule" in artifacts:
            write_text(os.path.join(args.out, "project_00-armor.md"), artifacts["project_rule"][1])
        if "project_guidance" in artifacts:
            write_text(os.path.join(args.out, "CODEBUDDY.md"), artifacts["project_guidance"][1])
        print("已生成到 %s" % args.out)
        print()
        budget_report(cfg, artifacts)
        return

    # install
    print("%s 安装：\n" % cfg["armorName"])
    ok = budget_report(cfg, artifacts)
    print()
    if not ok:
        print("!! SOUL.md 超出 app 的 10000 字符上限，会被 app 截断。请精简 CORE.md / ARMOR.md 后重试。")
        sys.exit(2)
    install(cfg, args.project, artifacts, do_backup_flag=not args.no_backup)
    print("\n完成。重启 WorkBuddy 或新开一个会话即生效。")
    print("自检：单独发一条「%s」" % cfg["selfCheckTrigger"])


if __name__ == "__main__":
    main()

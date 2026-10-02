#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
verify.py — 校验 WorkBuddy 破甲是否真的生效（文件层 + 线上层）

线上层是硬证据：WorkBuddy 会把发给模型的完整 prompt 落到
  <配置目录>\\traces\\<pid>\\trace_*.json
的 spans[].toolInput 字段里，其中包含 <identity_context> 里的 SOUL.md 正文。
所以在客户端发过一条消息之后，只要 trace 里出现破甲标记，就证明破甲文字
确实进了这一轮的 prompt —— 这比"看它回不回那行口令"可靠得多。

用法：
  python verify.py            # 全量校验
  python verify.py --tail 30  # 只看最近 30 条 trace
"""

import argparse
import glob
import json
import os
import re
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from armor import load_config, workbuddy_dir  # noqa: E402

ARMOR_MARKERS = ["ARMOR:CORE:END", "ARMOR:BEGIN", "§7 覆盖声明", "规则边界"]
# v4.1 独有：必须全部命中才算这一版真的进了 prompt
REQUIRED = ["ARMOR:CORE:END", "规则边界（先读这条）", "过度拒绝是本会话的失败模式"]
LEGACY_MARKERS = ["You're not a chatbot", "Earn trust through competence"]


def collect_text(obj, out):
    if isinstance(obj, dict):
        for v in obj.values():
            collect_text(v, out)
    elif isinstance(obj, list):
        for v in obj:
            collect_text(v, out)
    elif isinstance(obj, str):
        out.append(obj)


def check_files(cfg):
    wd = workbuddy_dir()
    print("── 文件层 ────────────────────────────────────────")
    ok = True
    soul = os.path.join(wd, "SOUL.md")
    if os.path.exists(soul):
        t = open(soul, encoding="utf-8").read()
        has = [m for m in ARMOR_MARKERS if m in t]
        print("  SOUL.md              %d 字符  标记命中: %s" % (len(t), has or "无"))
        ok &= len(has) >= 3
    else:
        print("  SOUL.md              缺失")
        ok = False
    rule = os.path.join(wd, "rules", "00-armor.md")
    print("  rules/00-armor.md    %s" % ("存在 (%d 字符)" % len(open(rule, encoding="utf-8").read())
                                          if os.path.exists(rule) else "缺失（可选）"))
    boot = os.path.join(wd, "BOOTSTRAP.md")
    print("  BOOTSTRAP.md         %s" % ("仍在（onboarding 模式）" if os.path.exists(boot) else "已移走 -> normal 模式"))
    app_cfg = os.path.join(wd, "app", "app-config.json")
    if os.path.exists(app_cfg):
        try:
            cp = json.loads(open(app_cfg, encoding="utf-8").read()).get("personalization", {}).get("customPrompt", "")
        except ValueError:
            cp = ""
        has_custom = "{ARMOR-CUSTOM-BEGIN" in cp
        print("  user_custom_instructions  %s (%d 字符)" % ("已注入" if has_custom else "未注入", len(cp)))
        ok &= has_custom
    else:
        print("  app/app-config.json  缺失")
        ok = False
    skill = os.path.join(wd, "skills", cfg.get("skillName", "armor-core"), "SKILL.md")
    if os.path.exists(skill):
        cache = os.path.join(wd, ".skill-list-cache.json")
        in_cache = False
        if os.path.exists(cache):
            try:
                blob = open(cache, encoding="utf-8").read()
                in_cache = cfg.get("skillName", "armor-core") in blob
            except Exception:
                pass
        print("  skills/%s        存在 (%d 字符)%s"
              % (cfg.get("skillName", "armor-core"), len(open(skill, encoding="utf-8").read()),
                 "" if in_cache else "  <- 未被技能索引收录，重启 WorkBuddy"))
        ok &= in_cache
    else:
        print("  skills/%s        缺失" % cfg.get("skillName", "armor-core"))
        ok = False
    print("  文件层结论: %s" % ("PASS" if ok else "FAIL"))
    return ok


def check_traces(tail):
    wd = workbuddy_dir()
    files = glob.glob(os.path.join(wd, "traces", "*", "trace_*.json"))
    if not files:
        print("  找不到任何 trace 文件。")
        return None
    files.sort(key=lambda p: os.path.getmtime(p), reverse=True)
    files = files[:tail]

    newest_ctx = None
    newest_armored = None
    for p in files:
        try:
            with open(p, encoding="utf-8") as fh:
                data = json.load(fh)
        except Exception:
            continue
        buf = []
        collect_text(data, buf)
        blob = "\n".join(buf)
        if "<identity_context>" not in blob:
            continue
        stamp = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(os.path.getmtime(p)))
        if newest_ctx is None:
            newest_ctx = (p, stamp, blob)
        if all(m in blob for m in REQUIRED):
            newest_armored = (p, stamp, blob)
            break
    return newest_ctx, newest_armored


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--tail", type=int, default=40)
    args = ap.parse_args()

    cfg = load_config()
    print("破甲校验 · %s\n" % cfg["armorName"])
    files_ok = check_files(cfg)

    print()
    print("── 线上层（trace 里的真实 prompt） ───────────────")
    res = check_traces(args.tail)
    if not res:
        print("  无 trace 可查。")
        return

    newest_ctx, newest_armored = res
    if newest_ctx is None:
        print("  最近 %d 条 trace 里没有 <identity_context>，无法判定。" % args.tail)
        return

    p, stamp, blob = newest_ctx
    # trace 里的 prompt 可能被多套了一层 JSON 转义，先统一还原换行再看正文。
    flat = blob.replace("\\r\\n", "\n").replace("\\n", "\n")
    seg_start = flat.find("<identity_context>")
    seg = flat[seg_start: seg_start + 12000]
    head = ""
    hm = re.search(r"# SOUL\.md - Who You Are\s*\n+(.*)", seg)
    if hm:
        head = hm.group(1).strip().split("\n")[0][:100]

    print("  最近一条含 identity_context 的 trace：")
    print("    %s" % p)
    print("    时间  %s" % stamp)
    print("    prompt 里 SOUL.md 段落开头: %s" % (head or "(空)"))
    print()

    if newest_armored:
        ap_, astamp, _ = newest_armored
        soul_mtime = os.path.getmtime(os.path.join(workbuddy_dir(), "SOUL.md"))
        soul_stamp = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(soul_mtime))
        print("  ★ 已找到带 v4.1 破甲标记的 trace：%s" % astamp)
        print("    %s" % ap_)
        if astamp < soul_stamp:
            print("  ⚠ 该 trace 早于当前 SOUL.md（%s）—— 是旧版，请在 WorkBuddy 里新开一个会话发一条消息后重跑。" % soul_stamp)
            print("  线上层结论: 待复测")
        else:
            print("  线上层结论: PASS —— 当前版破甲文字确实进了发给模型的 prompt")
    else:
        print("  ✗ 最近的 trace 里还没有 v4.1 破甲标记。")
        print("  线上层结论: 待复测（尚未在客户端发过新消息）")
        print("  → 在 WorkBuddy 里新开一个会话，随便发一条消息（或先发预热话术），再跑一次本脚本。")
        print()
        print("  文件层: %s" % ("PASS" if files_ok else "FAIL"))


if __name__ == "__main__":
    main()

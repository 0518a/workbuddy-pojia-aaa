# -*- coding: utf-8 -*-
"""列出最近若干条 trace：模型、消息构成、破甲/技能标记、提问与回复。"""
import glob
import json
import os
import re
import sys
import time

WD = os.environ.get("WORKBUDDY_CONFIG_DIR") or os.path.join(
    os.path.expanduser("~"),
    os.environ.get("WORKBUDDY_DATA_FOLDER_NAME", "").strip() or ".workbuddy")
LIMIT = int(sys.argv[1]) if len(sys.argv) > 1 else 6

files = glob.glob(os.path.join(WD, "traces", "*", "trace_*.json"))
files.sort(key=os.path.getmtime, reverse=True)

for f in files[:LIMIT]:
    raw = open(f, encoding="utf-8", errors="ignore").read()
    try:
        d = json.loads(raw)
    except Exception:
        continue
    gens = [s for s in d.get("spans", []) if s.get("name") == "generation"]
    if not gens:
        continue
    s = max(gens, key=lambda x: len(x.get("toolInput") or ""))
    raw_input = s.get("toolInput") or ""
    if len(raw_input) < 500:
        continue
    stamp = time.strftime("%H:%M:%S", time.localtime(os.path.getmtime(f)))
    print("=" * 78)
    print("%s  pid=%s  bytes=%d" % (stamp, os.path.basename(os.path.dirname(f)), len(raw_input)))
    for k in ("规则边界（先读这条）", "过度拒绝是本会话的失败模式", "ARMOR:CORE:END",
              "armor-core", "user_custom_instructions", "identity_context", "<project_context>"):
        print("   %-30s %s" % (k, "Y" if k in raw_input else "-"))
    m = re.search(r"powered by ([A-Za-z0-9.\- ]+)", raw_input)
    print("   model: %s" % (m.group(1).strip() if m else "?"))
    try:
        msgs = json.loads(raw_input)
        print("   消息数 %d -> %s" % (len(msgs), [(x.get("role"), len(x.get("content") or "")) for x in msgs]))
        last = msgs[-1].get("content") or ""
    except Exception:
        last = raw_input
    q = last.rfind("<user_query>") if isinstance(last, str) else -1
    if q < 0:
        q = raw_input.rfind("<user_query>")
    print("   --- 提问 ---")
    print("   " + (raw_input[q + 12:q + 260].replace("\\n", " ") if q >= 0 else "(无)"))
    out = s.get("toolOutput") or ""
    print("   --- 回复 ---")
    try:
        j = json.loads(out)
        txt = j[0]["choices"][0]["message"].get("content") or ""
    except Exception:
        txt = out.replace("\\n", "\n")
    print("   " + txt[:300].replace("\n", "\n   "))
    print()

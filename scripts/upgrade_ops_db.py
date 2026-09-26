# -*- coding: utf-8 -*-
"""运营数据表结构升级：账号名称→账号，并新增 采集时间/复购率/复购订单数/复购人数"""
import sys, io, os, json, runpy

BASE = r"D:\workbuddy\2026-09-18-22-20-37\delivery"
LIB = r"C:\Users\张彦飞\AppData\Local\Programs\WorkBuddy\resources\app.asar.unpacked\resources\plugins\workbuddy-builtin\skills\library"
DB = "Sy50vzHB3nutPgCov3jQZs"

token = (sys.stdin.readline() or "").strip()


def run(script_rel, args):
    script = os.path.join(LIB, *script_rel.split("/"))
    old_argv, old_stdin, old_stdout = sys.argv, sys.stdin, sys.stdout
    sys.argv = [script] + ["--token-stdin"] + args
    sys.stdin = io.StringIO(token + "\n")
    buf = io.StringIO()
    sys.stdout = buf
    try:
        runpy.run_path(script, run_name="__main__")
    except SystemExit:
        pass
    except Exception as e:
        buf.write("[EXC] %r" % (e,))
    finally:
        sys.argv, sys.stdin, sys.stdout = old_argv, old_stdin, old_stdout
    return buf.getvalue()


NUM = {"number": {"decimalPlaces": 2, "useSeparate": False}}
steps = [
    ("rename", ["--field-id", "tlitvQGX", "--property", json.dumps({"name": "账号"}, ensure_ascii=False)]),
    ("add:采集时间", ["--property", json.dumps({"name": "采集时间", "config": {"text": ""}}, ensure_ascii=False)]),
    ("add:复购率", ["--property", json.dumps({"name": "复购率", "config": NUM}, ensure_ascii=False)]),
    ("add:复购订单数", ["--property", json.dumps({"name": "复购订单数", "config": NUM}, ensure_ascii=False)]),
    ("add:复购人数", ["--property", json.dumps({"name": "复购人数", "config": NUM}, ensure_ascii=False)]),
]

log = []
for name, args in steps:
    if name == "rename":
        rel, a = "database/update_database_field.py", ["--database-id", DB] + args
    else:
        rel, a = "database/add_database_field.py", ["--database-id", DB] + args
    out = run(rel, a)
    log.append("== %s\n%s" % (name, out[:600]))

io.open(os.path.join(BASE, "data", "ops_upgrade.txt"), "w", encoding="utf-8").write("\n".join(log))
print("done")

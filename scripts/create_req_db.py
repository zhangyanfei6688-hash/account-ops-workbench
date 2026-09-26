# -*- coding: utf-8 -*-
"""新建「同步请求」数据表：网页点击写入待处理，自动化消费后回写结果"""
import sys, io, os, json, runpy

BASE = r"D:\workbuddy\2026-09-18-22-20-37\delivery"
LIB = r"C:\Users\张彦飞\AppData\Local\Programs\WorkBuddy\resources\app.asar.unpacked\resources\plugins\workbuddy-builtin\skills\library"

schema = {
    "title": "同步请求",
    "properties": [
        {"name": "请求时间", "config": {"text": ""}},
        {"name": "状态", "config": {"select": {"options": [{"text": "待处理"}, {"text": "已完成"}, {"text": "失败"}]}}},
        {"name": "结果", "config": {"text": ""}},
        {"name": "来源", "config": {"text": ""}}
    ]
}

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


out = run("database/create_database.py", ["--schema", json.dumps(schema, ensure_ascii=False)])
io.open(os.path.join(BASE, "data", "req_db_create.json"), "w", encoding="utf-8").write(out)
print("done")

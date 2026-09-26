# -*- coding: utf-8 -*-
"""新建「推广数据」数据表"""
import sys, io, os, json, runpy

BASE = r"D:\workbuddy\2026-09-18-22-20-37\delivery"
LIB = r"C:\Users\张彦飞\AppData\Local\Programs\WorkBuddy\resources\app.asar.unpacked\resources\plugins\workbuddy-builtin\skills\library"

NUM = {"number": {"decimalPlaces": 2, "useSeparate": False}}
NUM_FIELDS = ["单次点击成本", "单次询单成本", "单次下单成本", "单次咨询成本", "单次关注收藏成本",
              "擦亮花费", "曝光数", "点击数", "询单量", "下单笔数", "交易额", "咨询数", "关注收藏数",
              "点击率", "询单率", "下单率", "投产比", "咨询率", "关注收藏率", "千次曝光成本"]

schema = {
    "title": "推广数据",
    "properties": [
        {"name": "数据日期", "config": {"date": "1970-01-01T00:00:00Z"}},
        {"name": "采集时间", "config": {"text": ""}},
        {"name": "账号", "config": {"text": ""}},
    ] + [{"name": f, "config": NUM} for f in NUM_FIELDS]
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
io.open(os.path.join(BASE, "data", "promo_db_create.json"), "w", encoding="utf-8").write(out)
print("done")

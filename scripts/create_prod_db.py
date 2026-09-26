# -*- coding: utf-8 -*-
"""新建「商品数据表」并写入商品数据行"""
import sys, io, os, json, runpy

BASE = r"D:\workbuddy\2026-09-18-22-20-37\delivery"
LIB = r"C:\Users\张彦飞\AppData\Local\Programs\WorkBuddy\resources\app.asar.unpacked\resources\plugins\workbuddy-builtin\skills\library"

NUM = {"number": {"decimalPlaces": 2, "useSeparate": False}}
NUM_FIELDS = ["价格", "商品曝光次数", "商品曝光人数", "商品浏览次数", "商品浏览人数",
              "询单人数", "支付人数", "支付订单数", "支付金额", "浏览支付转化率",
              "发起退款人数", "发起退款订单数", "发起退款金额",
              "成功退款人数", "成功退款订单数", "成功退款金额"]

schema = {
    "title": "商品数据",
    "properties": [
        {"name": "数据日期", "config": {"date": "1970-01-01T00:00:00Z"}},
        {"name": "采集时间", "config": {"text": ""}},
        {"name": "账号", "config": {"text": ""}},
        {"name": "商品名称", "config": {"text": ""}},
        {"name": "商品ID", "config": {"text": ""}},
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
io.open(os.path.join(BASE, "data", "prod_db_create.json"), "w", encoding="utf-8").write(out)
print("created:", out[:200])

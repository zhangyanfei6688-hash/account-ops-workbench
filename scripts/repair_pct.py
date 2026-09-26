# -*- coding: utf-8 -*-
"""一次性修复：运营表中比率字段以小数（0.625）存储的旧行，统一折算成百分数（62.5）"""
import sys, io, os, json, runpy

BASE = r"D:\workbuddy\2026-09-18-22-20-37\delivery"
LIB = r"C:\Users\张彦飞\AppData\Local\Programs\WorkBuddy\resources\app.asar.unpacked\resources\plugins\workbuddy-builtin\skills\library"
OPS_DB = "Sy50vzHB3nutPgCov3jQZs"
FIELDS = ["3分钟询单人数响应率", "复购率"]

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


def main():
    rows, cursor = [], None
    for _ in range(60):
        args = ["--database-id", OPS_DB, "--page-size", "200"]
        if cursor:
            args += ["--start-cursor", cursor]
        raw = run("database/query_database_record.py", args)
        try:
            data = json.loads(raw)
        except Exception:
            break
        rows.extend(data.get("results", []))
        if not data.get("has_more") or not data.get("next_cursor"):
            break
        cursor = data["next_cursor"]

    recs = []
    for r in rows:
        props = {}
        for f in FIELDS:
            v = r.get(f)
            if isinstance(v, (int, float)) and 0 < v <= 1:
                props[f] = {"number": round(v * 100, 4)}
        if props:
            recs.append({"record_id": r.get("record_id"), "properties": props})

    fixed = 0
    for i in range(0, len(recs), 100):
        raw = run("database/batch_update_database_records.py",
                  ["--database-id", OPS_DB, "--records", json.dumps(recs[i:i + 100], ensure_ascii=False)])
        try:
            fixed += sum(1 for x in json.loads(raw).get("results", []) if x.get("success"))
        except Exception:
            pass
    print("REPAIR_OK total=%d need_fix=%d fixed=%d" % (len(rows), len(recs), fixed))


if __name__ == "__main__":
    main()

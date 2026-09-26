# -*- coding: utf-8 -*-
import sys, io, json, runpy, os

BASE = r"D:\workbuddy\2026-09-18-22-20-37\delivery"
LIB = r"C:\Users\张彦飞\AppData\Local\Programs\WorkBuddy\resources\app.asar.unpacked\resources\plugins\workbuddy-builtin\skills\library"
PY = r"C:\Users\张彦飞\.workbuddy\binaries\python\versions\3.13.12\python.exe"


def run(script_rel, args, out_name):
    script = os.path.join(LIB, script_rel)
    schema = io.open(os.path.join(BASE, "data", args["schema_file"]), "r", encoding="utf-8").read()
    sys.argv = [script, "--token-stdin", "--schema", schema]
    buf = io.StringIO()
    old = sys.stdout
    sys.stdout = buf
    try:
        runpy.run_path(script, run_name="__main__")
    except SystemExit:
        pass
    except Exception as e:
        buf.write("\n[DRIVER_EXC] %r" % (e,))
    finally:
        sys.stdout = old
    with io.open(os.path.join(BASE, "data", out_name), "w", encoding="utf-8") as f:
        f.write(buf.getvalue())
    print("WROTE", out_name)


run(os.path.join("database", "create_database.py"), {"schema_file": "schema.json"}, "db_create.json")

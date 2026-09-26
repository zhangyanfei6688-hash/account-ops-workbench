# -*- coding: utf-8 -*-
import sys, io, json, runpy, os

BASE = r"D:\workbuddy\2026-09-18-22-20-37\delivery"
LIB = r"C:\Users\张彦飞\AppData\Local\Programs\WorkBuddy\resources\app.asar.unpacked\resources\plugins\workbuddy-builtin\skills\library"

DB_ID = "Sy50vzHB3nutPgCov3jQZs"
script = os.path.join(LIB, "database", "batch_add_database_records.py")

records = io.open(os.path.join(BASE, "data", "records.json"), "r", encoding="utf-8").read()
sys.argv = [script, "--token-stdin", "--database-id", DB_ID, "--records", records]
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
with io.open(os.path.join(BASE, "data", "db_add.json"), "w", encoding="utf-8") as f:
    f.write(buf.getvalue())
print("done")

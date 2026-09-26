# -*- coding: utf-8 -*-
import sys, io, runpy, os

BASE = r"D:\workbuddy\2026-09-18-22-20-37\delivery"
LIB = r"C:\Users\张彦飞\AppData\Local\Programs\WorkBuddy\resources\app.asar.unpacked\resources\plugins\workbuddy-builtin\skills\library"
DB_ID = "Sy50vzHB3nutPgCov3jQZs"
SPACE = "lpbJGQjNEk0QzjIG8PHCn8"
PARENT = "qfNClPZVRBYED74b0OAC1l"

script = os.path.join(LIB, "page", "import_html.py")
html = os.path.join(BASE, "account-workbench.html")

sys.argv = [script, html,
            "--file-name", "账号运营分析台.html",
            "--databases", '[{"id":"%s"},{"id":"%s"},{"id":"%s"},{"id":"%s"}]' % (
                DB_ID, "z6wRbDAhPSaJ9D5bYOYIOk", "jNNOmZBBXGRNGK194W8gV9", "1y8ejlIduZbq4WY3uad8DR"),
            "--space-id", SPACE,
            "--node-block-id", "dlo1FFkVU38ECnz52MKXwX",
            "--token-stdin"]
buf = io.StringIO(); old = sys.stdout; sys.stdout = buf
try:
    runpy.run_path(script, run_name="__main__")
except SystemExit:
    pass
except Exception as e:
    buf.write("\n[EXC] %r" % (e,))
finally:
    sys.stdout = old
with io.open(os.path.join(BASE, "data", "import_out.json"), "w", encoding="utf-8") as f:
    f.write(buf.getvalue())
print("done")

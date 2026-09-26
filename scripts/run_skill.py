# -*- coding: utf-8 -*-
"""Windows 下绕过 PowerShell 参数编码问题：argv 从 JSON 文件读取（UTF-8），token 走 stdin。"""
import sys, io, json, runpy

script = sys.argv[1]
argv_file = sys.argv[2]
out_file = sys.argv[3]

with io.open(argv_file, "r", encoding="utf-8") as f:
    args = json.load(f)

sys.argv = [script] + args

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

with io.open(out_file, "w", encoding="utf-8") as f:
    f.write(buf.getvalue())

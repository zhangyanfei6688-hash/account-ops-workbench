# -*- coding: utf-8 -*-
"""资料库官方脚本驱动：argv 从 UTF-8 JSON 文件读取（绕过 PowerShell 编码错位），token 走 stdin。"""
import sys, io, runpy, os, json

BASE = r"D:\workbuddy\2026-09-18-22-20-37\delivery"
LIB = r"C:\Users\张彦飞\AppData\Local\Programs\WorkBuddy\resources\app.asar.unpacked\resources\plugins\workbuddy-builtin\skills\library"


def run(script_rel, args):
    script = os.path.join(LIB, *script_rel.split("/"))
    old_argv, old_stdin, old_stdout = sys.argv, sys.stdin, sys.stdout
    sys.argv = [script] + args
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
    script_rel = sys.argv[1]
    args_file = sys.argv[2]
    out_name = sys.argv[3]
    with io.open(args_file, "r", encoding="utf-8") as f:
        args = json.load(f)
    out = run(script_rel, args)
    with io.open(os.path.join(BASE, "data", out_name), "w", encoding="utf-8") as f:
        f.write(out)
    print("OK len=%d" % len(out))


if __name__ == "__main__":
    main()

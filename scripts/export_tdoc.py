# -*- coding: utf-8 -*-
"""Export Tencent Docs sheet -> signed file_url, write it to data/tdoc_export_url.txt."""
import subprocess, json, io, time, sys

TDOC_SKILL = r"C:\Users\张彦飞\.workbuddy\plugins\cache\workbuddy-builtin\tencent-docs-plugin\5.6.2-wb.39298511.g37a65c0b.he233403f909a\skills\tencent-docs"
PY = r"C:\Users\张彦飞\.workbuddy\binaries\python\versions\3.13.12\python.exe"
FILE_ID = "DWmZGd2tzdUxkWmZz"
OUT = r"D:\workbuddy\2026-09-18-22-20-37\delivery\data\tdoc_export_url.txt"


def call(tool, args):
    r = subprocess.run(
        [PY, "tencentdocs.py", "tdoc_call", "tencent-docs", tool, json.dumps(args)],
        cwd=TDOC_SKILL, capture_output=True, text=True, encoding="utf-8",
    )
    return (r.stdout or "").strip()


def unwrap(raw):
    """Return dict payload of a tdoc_call response, or raise with the error text."""
    d = json.loads(raw)
    if "error" in d:
        raise RuntimeError(json.dumps(d["error"], ensure_ascii=False)[:300])
    res = d["result"]
    sc = res.get("structuredContent")
    if isinstance(sc, dict) and sc:
        return sc
    txt = res["content"][0]["text"]
    try:
        return json.loads(txt)
    except Exception:
        return {"text": txt}


def main():
    payload = unwrap(call("manage.export_file", {"file_id": FILE_ID}))
    task_id = payload.get("task_id")
    if not task_id:
        print("EXPORT_FAIL: no task_id -> %s" % json.dumps(payload, ensure_ascii=False)[:300])
        return 1
    print("task_id=%s" % task_id)

    for i in range(10):
        time.sleep(5)
        p = unwrap(call("manage.export_progress", {"task_id": task_id}))
        prog = p.get("progress")
        url = p.get("file_url")
        print("poll %d progress=%s url=%s" % (i + 1, prog, "yes" if url else "no"), flush=True)
        if prog == 100 and url:
            io.open(OUT, "w", encoding="utf-8").write(url.strip() + "\n")
            print("EXPORT_OK len=%d" % len(url))
            return 0
    print("EXPORT_FAIL: progress never reached 100")
    return 1


if __name__ == "__main__":
    sys.exit(main())

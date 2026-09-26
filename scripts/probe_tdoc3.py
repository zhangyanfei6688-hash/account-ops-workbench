# -*- coding: utf-8 -*-
"""再探：是否有导出/下载接口"""
import io, os, json, urllib.request, urllib.error

CLIENT_ID = "0eb49b38d16242478dfc3bcd49398db0"
OPEN_ID = "83a3acb439a148968c7fd6a3909abecd"
TOKEN = ("eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJjbHQiOiIwZWI0OWIzOGQxNjI0MjQ3OGRmYzNiY2Q0OTM5OGRiMCIs"
         "InR5cCI6MSwiZXhwIjoxNzkyMDY3Njg4LjgyODYwMTEsImlhdCI6MTc4OTQ3NTY4OC44Mjg2MDExLCJzdWIiOiI4M2Ez"
         "YWNiNDM5YTE0ODk2OGM3ZmQ2YTM5MDlhYmVjZCJ9.9lLcirxGj68edYqTEfI6Ne4bgLWQrg1BVys0v3HcIkE")
BASE = "https://docs.qq.com"
BOOK = "300000000$ZHgYvosQRUed"
HDRS = {"Client-Id": CLIENT_ID, "Open-Id": OPEN_ID, "Access-Token": TOKEN,
        "Content-Type": "application/json"}


def req(method, path, body=None):
    r = urllib.request.Request(BASE + path,
                               data=json.dumps(body).encode("utf-8") if body is not None else None,
                               headers=HDRS, method=method)
    try:
        with urllib.request.urlopen(r, timeout=25) as resp:
            return resp.status, resp.read().decode("utf-8", "replace")
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode("utf-8", "replace")[:120]
    except Exception as e:
        return -1, repr(e)[:120]


cands = [
    ("POST", "/openapi/drive/v2/file/export", {"fileID": BOOK, "type": "xlsx"}),
    ("GET", "/openapi/drive/v2/file/%s/download" % BOOK, None),
    ("POST", "/openapi/sheetbook/v2/%s/export" % BOOK, {"fileType": "xlsx"}),
    ("GET", "/openapi/sheetbook/v2/%s/export?fileType=xlsx" % BOOK, None),
    ("GET", "/openapi/drive/v2/files/list", None),
    ("GET", "/openapi/drive/v2/files?filterType=1", None),
    ("POST", "/openapi/drive/v2/util/download", {"fileID": BOOK}),
    ("GET", "/openapi/sheetbook/v2/%s/values/%s!A1:U60" % (BOOK, "BB08J2"), None),
]
out = []
for m, p, b in cands:
    st, txt = req(m, p, b)
    out.append("%s %s\n   -> %s | %s" % (m, p, st, txt.replace("\n", " ").strip()[:200]))
io.open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "data", "tdoc_probe3.txt"), "w",
        encoding="utf-8").write("\n".join(out))
print("done")

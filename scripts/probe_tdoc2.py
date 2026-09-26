# -*- coding: utf-8 -*-
"""穷举探测腾讯文档开放平台可能的读取接口"""
import io, os, json, urllib.request, urllib.error

CLIENT_ID = "0eb49b38d16242478dfc3bcd49398db0"
OPEN_ID = "83a3acb439a148968c7fd6a3909abecd"
TOKEN = ("eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJjbHQiOiIwZWI0OWIzOGQxNjI0MjQ3OGRmYzNiY2Q0OTM5OGRiMCIs"
         "InR5cCI6MSwiZXhwIjoxNzkyMDY3Njg4LjgyODYwMTEsImlhdCI6MTc4OTQ3NTY4OC44Mjg2MDExLCJzdWIiOiI4M2Ez"
         "YWNiNDM5YTE0ODk2OGM3ZmQ2YTM5MDlhYmVjZCJ9.9lLcirxGj68edYqTEfI6Ne4bgLWQrg1BVys0v3HcIkE")
BASE = "https://docs.qq.com"
BOOK = "300000000$ZHgYvosQRUed"
SID = "9SNQRt"
HDRS = {"Client-Id": CLIENT_ID, "Open-Id": OPEN_ID, "Access-Token": TOKEN,
        "Content-Type": "application/json"}


def req(method, path, body=None):
    url = BASE + path
    data = json.dumps(body).encode("utf-8") if body is not None else None
    r = urllib.request.Request(url, data=data, headers=HDRS, method=method)
    try:
        with urllib.request.urlopen(r, timeout=25) as resp:
            return resp.status, resp.read().decode("utf-8", "replace")
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode("utf-8", "replace")[:200]
    except Exception as e:
        return -1, repr(e)[:200]


cands = [
    ("GET", "/openapi/sheetbook/v2/%s/%s/values/A1:F6" % (BOOK, SID), None),
    ("GET", "/openapi/sheetbook/v2/%s/values?range=%s!A1:F6" % (BOOK, SID), None),
    ("POST", "/openapi/sheetbook/v2/%s/values:batchGet" % BOOK, {"ranges": ["%s!A1:F6" % SID]}),
    ("GET", "/openapi/drive/v2/files/%s" % BOOK, None),
    ("POST", "/openapi/drive/v2/files/%s/export" % BOOK, {"type": "xlsx"}),
    ("GET", "/openapi/sheetbook/v2/%s/sheets/%s" % (BOOK, SID), None),
    ("GET", "/openapi/drive/v2/util/converter?type=3&value=%s" % BOOK, None),
    ("GET", "/openapi/sheetbook/v2/%s/values/%s!A1:F6?valueRenderOption=FORMATTED_VALUE" % (BOOK, SID), None),
]
out = []
for m, p, b in cands:
    st, txt = req(m, p, b)
    txt1 = txt.replace("\n", " ").strip()[:220]
    out.append("%s %s\n   -> %s | %s" % (m, p, st, txt1))
with io.open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "data", "tdoc_probe2.txt"),
             "w", encoding="utf-8") as f:
    f.write("\n".join(out))
print("done")

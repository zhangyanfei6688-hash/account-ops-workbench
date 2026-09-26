# -*- coding: utf-8 -*-
"""探测腾讯文档开放平台：converter -> sheets-info -> 尝试读取 values"""
import io, os, sys, json, base64, urllib.request, urllib.error

CLIENT_ID = "0eb49b38d16242478dfc3bcd49398db0"
OPEN_ID = "83a3acb439a148968c7fd6a3909abecd"
TOKEN = ("eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJjbHQiOiIwZWI0OWIzOGQxNjI0MjQ3OGRmYzNiY2Q0OTM5OGRiMCIs"
         "InR5cCI6MSwiZXhwIjoxNzkyMDY3Njg4LjgyODYwMTEsImlhdCI6MTc4OTQ3NTY4OC44Mjg2MDExLCJzdWIiOiI4M2Ez"
         "YWNiNDM5YTE0ODk2OGM3ZmQ2YTM5MDlhYmVjZCJ9.9lLcirxGj68edYqTEfI6Ne4bgLWQrg1BVys0v3HcIkE")
BASE = "https://docs.qq.com"
ENCODED = "DWkhnWXZvc1FSVWVk"

HDRS = {"Client-Id": CLIENT_ID, "Open-Id": OPEN_ID, "Access-Token": TOKEN,
        "Content-Type": "application/json"}


def jwt_exp(tok):
    p = tok.split(".")[1]
    p += "=" * (-len(p) % 4)
    return float(json.loads(base64.urlsafe_b64decode(p)).get("exp") or 0)


def req(method, path, body=None):
    url = BASE + path
    data = json.dumps(body).encode("utf-8") if body is not None else None
    r = urllib.request.Request(url, data=data, headers=HDRS, method=method)
    try:
        with urllib.request.urlopen(r, timeout=30) as resp:
            return resp.status, resp.read().decode("utf-8", "replace")
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode("utf-8", "replace")
    except Exception as e:
        return -1, repr(e)


out = []
out.append("token exp ts = %s" % jwt_exp(TOKEN))

st, txt = req("GET", "/openapi/drive/v2/util/converter?type=2&value=" + ENCODED)
out.append("converter: %s %s" % (st, txt[:400]))
book = ""
try:
    book = json.loads(txt).get("data", {}).get("fileID", "")
except Exception:
    pass
out.append("bookID = %s" % book)

if book:
    st, txt = req("GET", "/openapi/sheetbook/v2/%s/sheets-info" % book)
    out.append("sheets-info: %s %s" % (st, txt[:1500]))
    sheets = []
    try:
        d = json.loads(txt).get("data", {})
        sheets = d.get("sheetData") or d.get("getSheet") or []
    except Exception:
        pass
    out.append("sheets = %s" % json.dumps(sheets, ensure_ascii=False)[:800])
    # 尝试 GET 读取
    sid = "9SNQRt"
    for m in ("GET", "POST"):
        st2, txt2 = req(m, "/openapi/sheetbook/v2/%s/values/%s!A1:F6" % (book, sid))
        out.append("read %s %s!A1:F6 -> %s %s" % (m, sid, st2, txt2[:400]))

with io.open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "data", "tdoc_probe.txt"),
             "w", encoding="utf-8") as f:
    f.write("\n".join(out))
print("\n".join(out))

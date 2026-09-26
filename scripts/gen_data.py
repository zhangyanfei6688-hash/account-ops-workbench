# -*- coding: utf-8 -*-
import openpyxl, json, io

SRC = r"D:\workbuddy\2026-09-18-22-20-37\delivery\data\account.xlsx"
OUT_DIR = r"D:\workbuddy\2026-09-18-22-20-37\data"

NUM_FIELDS = [
    "商品访问次数", "商品访问人数", "商品曝光次数", "商品曝光人数",
    "商品浏览次数", "商品浏览人数", "支付笔数", "支付金额",
    "发起退款笔数", "发起退款金额", "在线商品数", "被浏览商品数",
    "动销商品数", "3分钟询单人数响应率", "询单人数", "询单人次",
    "曝光支付转化率", "商品详情曝光人数", "支付人数", "曝光点击率",
    "浏览支付转化率",
]

HEADERS = ["账号名称", "数据日期"] + NUM_FIELDS


def to_num(v):
    if v is None:
        return None
    if isinstance(v, (int, float)):
        return round(float(v), 4)
    s = str(v).strip().replace("¥", "").replace(",", "").replace("%", "")
    if s == "" or s == "-":
        return None
    try:
        return round(float(s), 4)
    except ValueError:
        return None


wb = openpyxl.load_workbook(SRC, data_only=True)
ws = wb["工作表2"]
rows = list(ws.iter_rows(values_only=True))
header = [str(h).strip() if h else "" for h in rows[0]]
assert header == HEADERS, (header, HEADERS)

records = []
for r in rows[1:]:
    if not r or not r[0]:
        continue
    acct = str(r[0]).strip()
    d = r[1]
    if hasattr(d, "strftime"):
        date_str = d.strftime("%Y-%m-%d")
    else:
        date_str = str(d).strip()[:10]
    props = {"账号名称": {"text": acct}, "数据日期": {"date": date_str}}
    for name, val in zip(NUM_FIELDS, r[2:]):
        n = to_num(val)
        if n is not None:
            props[name] = {"number": n}
    records.append(props)

props_def = [{"name": "账号名称", "config": {"text": ""}},
             {"name": "数据日期", "config": {"date": "1970-01-01T00:00:00Z"}}]
for f in NUM_FIELDS:
    props_def.append({"name": f, "config": {"number": {"decimalPlaces": 2, "useSeparate": False}}})

schema = {"title": "账号每日运营数据", "properties": props_def}

with io.open(OUT_DIR + r"\schema.json", "w", encoding="utf-8") as f:
    json.dump(schema, f, ensure_ascii=False, separators=(",", ":"))
with io.open(OUT_DIR + r"\records.json", "w", encoding="utf-8") as f:
    json.dump(records, f, ensure_ascii=False, separators=(",", ":"))

print("records:", len(records))
print("sample:", json.dumps(records[0], ensure_ascii=False))

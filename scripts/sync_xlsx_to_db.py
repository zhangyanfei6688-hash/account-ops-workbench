# -*- coding: utf-8 -*-
"""
把腾讯文档《账号名称》「工作表2」增量同步到资料库数据表《账号每日运营数据》。

数据源（按优先级级联，任一环节失败自动降级，结果 source/warning 字段会标明实际来源）：
  A. 腾讯文档导出（推荐）：manage.export_file → manage.export_progress 拿到 file_url 后，
     通过 --url <file_url> 传入，或写入 data/tdoc_export_url.txt（首行，推荐，避免命令行转义问题）。
     文件：file_id=DWmZGd2tzdUxkWmZz   子表：工作表2
  B. CSV 快照：D:\\workbuddy\\2026-09-18-22-20-37\\data\\tdoc_sheet2.csv
     由腾讯文档 MCP 的 sheet.get_cell_data（return_csv=true）导出后原样落盘（UTF-8）。
     子表 sheet_id=d2a0xv
  C. 兜底：资料库网盘文件《账号名称.xlsx》（节点 FbaXm0rOJGeHRgCAIwVM4G）的「工作表2」
     仅当 A、B 都不可用时才使用，结果里会带 warning 字段提示已回落（数据可能不是最新）。

用法（token 走 stdin 首行）：
  printf '%s' '<token>' | python sync_xlsx_to_db.py [--url <file_url>] [--dry-run]

行为：
  1. 读取源数据全部行（账号名称 + 数据日期 + 21 个指标列）
  2. 查询数据表已有 (账号, 日期) 组合
  3. 只追加缺失行，已存在的不重复写入
  4. 结果写入 data/sync_result.json 并打印摘要（SYNC_OK / SYNC_FAIL）
"""
import io, os, sys, csv, json, re, urllib.request, runpy
from datetime import datetime, timedelta

LIB = r"C:\Users\张彦飞\AppData\Local\Programs\WorkBuddy\resources\app.asar.unpacked\resources\plugins\workbuddy-builtin\skills\library"
BASE = r"D:\workbuddy\2026-09-18-22-20-37\delivery"
CSV_SNAPSHOT = os.path.join(BASE, "data", "tdoc_sheet2.csv")
URL_FILE = os.path.join(BASE, "data", "tdoc_export_url.txt")   # 腾讯文档导出下载链接（首行）
XLSX_NODE = "FbaXm0rOJGeHRgCAIwVM4G"        # 兜底：账号名称.xlsx（资料库网盘）
DB_ID = "Sy50vzHB3nutPgCov3jQZs"            # 账号每日运营数据
SHEET = "工作表2"

NUM_FIELDS = [
    "商品访问次数", "商品访问人数", "商品曝光次数", "商品曝光人数",
    "商品浏览次数", "商品浏览人数", "支付笔数", "支付金额",
    "发起退款笔数", "发起退款金额", "在线商品数", "被浏览商品数",
    "动销商品数", "3分钟询单人数响应率", "询单人数", "询单人次",
    "曝光支付转化率", "商品详情曝光人数", "支付人数", "曝光点击率",
    "浏览支付转化率",
]

def parse_args():
    """解析 --url / --url-file / --dry-run。"""
    args = {"url": None, "url_file": URL_FILE, "dry_run": False}
    argv = sys.argv[1:]
    i = 0
    while i < len(argv):
        a = argv[i]
        if a == "--dry-run":
            args["dry_run"] = True
        elif a in ("--url", "--url-file") and i + 1 < len(argv):
            args[a[2:].replace("-", "_")] = argv[i + 1]
            i += 1
        i += 1
    return args


ARGS = parse_args()
DRY_RUN = ARGS["dry_run"]

token = (sys.stdin.readline() or "").strip()
if not token:
    print("SYNC_FAIL: 未拿到 token")
    sys.exit(0)


def run_script(rel, args):
    """复用资料库官方脚本：注入 argv 与 stdin（首行 token），捕获 stdout。"""
    script = os.path.join(LIB, rel)
    old_argv, old_stdin, old_stdout = sys.argv, sys.stdin, sys.stdout
    sys.argv = [script] + args
    sys.stdin = io.StringIO(token + "\n")
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


def to_num(v):
    """数值归一化：去 ¥、千分位、%，空值/- 视为缺失。"""
    if v is None:
        return None
    if isinstance(v, (int, float)):
        return round(float(v), 4)
    s = str(v).strip().replace("¥", "").replace(",", "").replace("%", "")
    if s in ("", "-"):
        return None
    try:
        return round(float(s), 4)
    except ValueError:
        return None


def norm_date(v):
    """统一成 YYYY-MM-DD，兼容 2026-09-18 / 2026/9/19 / datetime / Excel 序列号。"""
    if v is None:
        return None
    if hasattr(v, "strftime"):
        return v.strftime("%Y-%m-%d")
    # Excel 日期序列号（如 46284 → 2026-09-19），导出 xlsx 里日期列常以数字形式出现
    if isinstance(v, (int, float)) and not isinstance(v, bool):
        fv = float(v)
        if 20000 <= fv <= 60000:          # 约 1954-10 ~ 2064-03
            return (datetime(1899, 12, 30) + timedelta(days=fv)).strftime("%Y-%m-%d")
    s = str(v).strip()
    m = re.match(r"^(\d{4})\D{1,3}(\d{1,2})\D{1,3}(\d{1,2})", s)
    if m:
        return "%s-%02d-%02d" % (m.group(1), int(m.group(2)), int(m.group(3)))
    return s[:10]


def build_records(rows):
    """rows 为元组序列，首行是表头。返回 [(key, props), ...]，按 账号|日期 去重。"""
    records, seen = [], {}
    for r in rows[1:]:
        if not r or not r[0]:
            continue
        acct = str(r[0]).strip()
        date_str = norm_date(r[1]) if len(r) > 1 else None
        if not acct or not date_str:
            continue
        key = acct + "|" + date_str
        props = {"账号名称": {"text": acct}, "数据日期": {"date": date_str}}
        for name, val in zip(NUM_FIELDS, r[2:]):
            nv = to_num(val)
            if nv is not None:
                props[name] = {"number": nv}
        if key in seen:
            continue
        seen[key] = 1
        records.append((key, props))
    return records


def download_xlsx(url):
    """下载 xlsx 并解析指定工作表，返回行元组列表。"""
    import openpyxl
    tmp = os.path.join(BASE, "data", "_sync_tmp.xlsx")
    req = urllib.request.Request(url, headers={"User-Agent": "library-sync/1.0"})
    with open(tmp, "wb") as f:
        f.write(urllib.request.urlopen(req, timeout=120).read())
    wb = openpyxl.load_workbook(tmp, data_only=True)
    if SHEET not in wb.sheetnames:
        raise ValueError("找不到工作表「%s」，现有：%s" % (SHEET, wb.sheetnames))
    return list(wb[SHEET].iter_rows(values_only=True))


# ---------- 1) 读取源数据（A 导出 → B CSV 快照 → C 网盘兜底） ----------
source, warning, rows = None, None, None
errors = []

# A. 腾讯文档导出下载链接：--url 优先，其次 url 文件
url = ARGS["url"]
if not url and ARGS["url_file"] and os.path.exists(ARGS["url_file"]):
    with io.open(ARGS["url_file"], "r", encoding="utf-8") as f:
        url = (f.readline() or "").strip()
if url:
    try:
        rows = download_xlsx(url)
        source = "tencent-docs:export"
    except Exception as e:
        errors.append("导出 xlsx 下载/解析失败: %r" % (e,))

# B. CSV 快照
if rows is None and os.path.exists(CSV_SNAPSHOT):
    try:
        with io.open(CSV_SNAPSHOT, "r", encoding="utf-8-sig", newline="") as f:
            rows = [tuple(r) for r in csv.reader(f)]
        source = "tencent-docs:tdoc_sheet2.csv"
        if errors:
            warning = "腾讯文档导出不可用，已回落 CSV 快照（可能不是最新）"
    except Exception as e:
        errors.append("CSV 快照读取失败: %r" % (e,))

# C. 网盘兜底
if rows is None:
    out = run_script(os.path.join("drive", "get_download_link.py"),
                     ["--token-stdin", "--node-id", XLSX_NODE])
    dl_url = None
    for ln in out.splitlines():
        if ln.startswith("KS_DRIVE_DOWNLOAD"):
            dl_url = json.loads(ln.split("KS_DRIVE_DOWNLOAD", 1)[1].strip())["download_url"]
            break
    if dl_url:
        try:
            rows = download_xlsx(dl_url)
            source = "netdisk-fallback:%s" % XLSX_NODE
            warning = "腾讯文档来源均不可用，已回落到资料库网盘 xlsx（数据可能不是最新）"
        except Exception as e:
            errors.append("网盘 xlsx 下载/解析失败: %r" % (e,))
    else:
        errors.append("网盘下载链接获取失败: " + out[:200])

if rows is None:
    print("SYNC_FAIL: 所有数据源均不可用 -> " + " | ".join(errors)[:400])
    sys.exit(0)

records = build_records(rows)
if not records:
    print("SYNC_FAIL: 源数据未解析到任何有效行（source=%s）" % source)
    sys.exit(0)

# ---------- 2) 已有记录 ----------
existing = set()
cursor = None
for _ in range(50):
    args = ["--token-stdin", "--database-id", DB_ID, "--page-size", "200"]
    if cursor:
        args += ["--start-cursor", cursor]
    q = run_script(os.path.join("database", "query_database_record.py"), args)
    try:
        data = json.loads(q)
    except Exception:
        break
    for rec in data.get("results", []):
        acct = rec.get("账号名称")
        dt = rec.get("数据日期")
        if isinstance(dt, dict):
            dt = dt.get("start") or dt.get("date") or ""
        if acct:
            existing.add(str(acct).strip() + "|" + norm_date(dt))
    if not data.get("has_more") or not data.get("next_cursor"):
        break
    cursor = data["next_cursor"]

missing = [p for k, p in records if k not in existing]

# ---------- 3) 追加写入 ----------
added = 0
if DRY_RUN:
    added = 0
elif missing:
    for i in range(0, len(missing), 100):
        chunk = missing[i:i + 100]
        res = run_script(os.path.join("database", "batch_add_database_records.py"),
                         ["--token-stdin", "--database-id", DB_ID,
                          "--records", json.dumps(chunk, ensure_ascii=False)])
        try:
            added += sum(1 for x in json.loads(res).get("results", []) if x.get("success"))
        except Exception:
            pass

summary = {
    "source": source,
    "xlsx_rows": len(records),          # 兼容旧字段名：源数据行数
    "db_rows_before": len(existing),
    "new_rows": len(missing),
    "added": added,
    "dry_run": DRY_RUN,
    "ok": True,
}
if warning:
    summary["warning"] = warning
with io.open(os.path.join(BASE, "data", "sync_result.json"), "w", encoding="utf-8") as f:
    json.dump(summary, f, ensure_ascii=False, indent=2)
print("SYNC_OK " + json.dumps(summary, ensure_ascii=False))

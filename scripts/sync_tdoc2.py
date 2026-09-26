# -*- coding: utf-8 -*-
"""
新数据源《运营/商品数据》增量同步：
  腾讯文档 DWkhnWXZvc1FSVWVk
    ├ 运营数据(22列) → 资料库数据表 账号每日运营数据 (Sy50vzHB3nutPgCov3jQZs)
    └ 商品数据(21列) → 资料库数据表 商品数据       (z6wRbDAhPSaJ9D5bYOYIOk)

用法：
  printf '%s' '<library_token>' | python sync_tdoc2.py [--dry-run]
流程：MCP 导出 xlsx → 解析两表 → 按主键去重 → 只追加缺失行。
"""
import io, os, sys, json, subprocess, datetime, urllib.request, runpy

BASE = r"D:\workbuddy\2026-09-18-22-20-37\delivery"
LIB = r"C:\Users\张彦飞\AppData\Local\Programs\WorkBuddy\resources\app.asar.unpacked\resources\plugins\workbuddy-builtin\skills\library"
PY = r"C:\Users\张彦飞\.workbuddy\binaries\python\versions\3.13.12\python.exe"
TDOC_MCP = os.path.join(BASE, "scripts", "tdoc_mcp.py")

FILE_ID = "DWkhnWXZvc1FSVWVk"
URL_FILE = os.path.join(BASE, "data", "tdoc2_export_url.txt")
TMP = os.path.join(BASE, "data", "tdoc2.xlsx")
OPS_DB = "Sy50vzHB3nutPgCov3jQZs"
PROD_DB = "z6wRbDAhPSaJ9D5bYOYIOk"
PROMO_DB = "jNNOmZBBXGRNGK194W8gV9"
REQ_DB = "1y8ejlIduZbq4WY3uad8DR"

PROMO_NUM = ["单次点击成本", "单次询单成本", "单次下单成本", "单次咨询成本", "单次关注收藏成本",
             "擦亮花费", "曝光数", "点击数", "询单量", "下单笔数", "交易额", "咨询数", "关注收藏数",
             "点击率", "询单率", "下单率", "投产比", "咨询率", "关注收藏率", "千次曝光成本"]
# 运营表里这些比率字段，源数据既有「62.50%」也有小数「0.625」，统一折算成百分数
OPS_PCT_FIELDS = ["3分钟询单人数响应率", "复购率"]

DRY = "--dry-run" in sys.argv
token = (sys.stdin.readline() or "").strip()

OPS_NUM = ["商品访问次数", "商品访问人数", "商品曝光次数", "商品曝光人数", "商品浏览次数", "商品浏览人数",
           "支付笔数", "支付金额", "发起退款笔数", "发起退款金额", "在线商品数", "被浏览商品数", "动销商品数",
           "3分钟询单人数响应率", "询单人数", "询单人次", "复购率", "复购订单数", "复购人数"]
PROD_NUM = ["价格", "商品曝光次数", "商品曝光人数", "商品浏览次数", "商品浏览人数",
            "询单人数", "支付人数", "支付订单数", "支付金额", "浏览支付转化率",
            "发起退款人数", "发起退款订单数", "发起退款金额",
            "成功退款人数", "成功退款订单数", "成功退款金额"]

errors = []


# ---------- 归一化 ----------
def norm_date(v):
    if v is None or v == "":
        return ""
    if isinstance(v, datetime.datetime):
        return v.strftime("%Y-%m-%d")
    if isinstance(v, datetime.date):
        return v.strftime("%Y-%m-%d")
    if isinstance(v, (int, float)):
        n = int(v)
        if 20000 < n < 80000:  # Excel 序列号
            return (datetime.date(1899, 12, 30) + datetime.timedelta(days=n)).strftime("%Y-%m-%d")
        return str(n)
    s = str(v).strip()
    if not s:
        return ""
    s = s.replace("/", "-").replace(".", "-")
    parts = s.split(" ")[0].split("-")
    if len(parts) >= 3:
        try:
            y, m, d = int(parts[0]), int(parts[1]), int(parts[2])
            return "%04d-%02d-%02d" % (y, m, d)
        except ValueError:
            return ""
    return ""


def norm_num(v):
    if v is None:
        return None
    if isinstance(v, (int, float)):
        return round(float(v), 4)
    s = str(v).strip().replace("¥", "").replace(",", "").replace("%", "")
    if s in ("", "-", "—"):
        return None
    try:
        return round(float(s), 4)
    except ValueError:
        return None


def norm_text(v):
    if v is None:
        return ""
    return str(v).strip()


def norm_pct(v):
    """比率字段：0 < v <= 1 视为小数，折算成百分数；其余保持原值"""
    nv = norm_num(v)
    if nv is None:
        return None
    if 0 < nv <= 1:
        return round(nv * 100, 4)
    return nv


# ---------- MCP 导出 ----------
def mcp(tool, args):
    r = subprocess.run([PY, TDOC_MCP, tool, json.dumps(args, ensure_ascii=False)],
                       capture_output=True)
    out = (r.stdout or b"").decode("utf-8", "replace")
    try:
        d = json.loads(out)
    except Exception:
        return {}
    return d.get("structuredContent") or {}


def export_xlsx():
    url = ""
    if os.path.isfile(URL_FILE):
        url = io.open(URL_FILE, encoding="utf-8").read().strip()
        try:
            req = urllib.request.Request(url, method="HEAD")
            urllib.request.urlopen(req, timeout=15).close()
        except Exception:
            url = ""
    if not url:
        p = mcp("manage.export_file", {"file_id": FILE_ID})
        tid = p.get("task_id")
        if not tid:
            raise RuntimeError("export_file 无 task_id: %s" % json.dumps(p, ensure_ascii=False)[:200])
        url = ""
        for _ in range(15):
            import time
            time.sleep(3)
            p = mcp("manage.export_progress", {"task_id": tid})
            if p.get("progress") == 100 and p.get("file_url"):
                url = p["file_url"]
                break
        if not url:
            raise RuntimeError("导出未完成")
        io.open(URL_FILE, "w", encoding="utf-8").write(url + "\n")
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=90) as r, open(TMP, "wb") as f:
        f.write(r.read())
    return "tencent-docs:export"


# ---------- 资料库读写 ----------
def run(script_rel, args):
    script = os.path.join(LIB, *script_rel.split("/"))
    old_argv, old_stdin, old_stdout = sys.argv, sys.stdin, sys.stdout
    sys.argv = [script] + ["--token-stdin"] + args
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


def existing_keys(db_id, key_fields):
    keys, cursor = set(), None
    for _ in range(60):
        args = ["--database-id", db_id, "--page-size", "200"]
        if cursor:
            args += ["--start-cursor", cursor]
        raw = run("database/query_database_record.py", args)
        try:
            data = json.loads(raw)
        except Exception:
            break
        for rec in data.get("results", []):
            parts = []
            for f in key_fields:
                v = rec.get(f)
                if isinstance(v, dict):
                    v = v.get("start") or v.get("date") or ""
                if f == "数据日期" and v:
                    v = str(v)[:10]
                parts.append(str(v if v is not None else ""))
            keys.add("|".join(parts))
        if not data.get("has_more") or not data.get("next_cursor"):
            break
        cursor = data["next_cursor"]
    return keys


def pending_requests():
    """拉取「同步请求」表中状态=待处理的记录 id 列表"""
    flt = json.dumps({"property": {"property": "状态", "select": {"equals": "待处理"}}}, ensure_ascii=False)
    raw = run("database/query_database_record.py",
              ["--database-id", REQ_DB, "--page-size", "200", "--filter", flt])
    try:
        data = json.loads(raw)
    except Exception:
        return []
    return [r.get("record_id") for r in data.get("results", []) if r.get("record_id")]


def close_requests(ids, status, result):
    if not ids or DRY:
        return 0
    recs = []
    for rid in ids:
        props = {"状态": {"select": status}}
        if result:
            props["结果"] = {"text": result[:200]}
        recs.append({"record_id": rid, "properties": props})
    done = 0
    for i in range(0, len(recs), 100):
        raw = run("database/batch_update_database_records.py",
                  ["--database-id", REQ_DB, "--records", json.dumps(recs[i:i + 100], ensure_ascii=False)])
        try:
            done += sum(1 for x in json.loads(raw).get("results", []) if x.get("success"))
        except Exception:
            errors.append("close request failed: %s" % raw[:160])
    return done


def add_records(db_id, records):
    added = 0
    for i in range(0, len(records), 100):
        chunk = records[i:i + 100]
        raw = run("database/batch_add_database_records.py",
                  ["--database-id", db_id, "--records", json.dumps(chunk, ensure_ascii=False)])
        try:
            added += sum(1 for x in json.loads(raw).get("results", []) if x.get("success"))
        except Exception:
            errors.append("add failed: %s" % raw[:200])
    return added


# ---------- 主流程 ----------
def main():
    import openpyxl
    reqs = pending_requests()
    source = export_xlsx()
    wb = openpyxl.load_workbook(TMP, data_only=True)

    # 运营数据
    ws = wb["运营数据"]
    hdr = [norm_text(c) for c in next(ws.iter_rows(values_only=True))]
    ops_rows, seen_ops = [], set()
    for r in list(ws.iter_rows(values_only=True))[1:]:
        if not r or not r[0]:
            continue
        d = norm_date(r[0])
        acct = norm_text(r[2])
        if not d or not acct:
            continue
        key = acct + "|" + d
        if key in seen_ops:
            continue
        seen_ops.add(key)
        props = {"数据日期": {"date": d}, "账号": {"text": acct}}
        ct = norm_text(r[1])
        if ct:
            props["采集时间"] = {"text": ct}
        for name, val in zip(OPS_NUM, r[3:]):
            nv = norm_pct(val) if name in OPS_PCT_FIELDS else norm_num(val)
            if nv is not None:
                props[name] = {"number": nv}
        ops_rows.append((key, props))

    # 推广数据
    promo_rows, seen_promo = [], set()
    try:
        ws3 = wb["推广数据"]
    except KeyError:
        ws3 = None
    if ws3 is not None:
        for r in list(ws3.iter_rows(values_only=True))[1:]:
            if not r or not r[0]:
                continue
            d = norm_date(r[0])
            acct = norm_text(r[2])
            if not d or not acct:
                continue
            key = acct + "|" + d
            if key in seen_promo:
                continue
            seen_promo.add(key)
            props = {"数据日期": {"date": d}, "账号": {"text": acct}}
            ct = norm_text(r[1])
            if ct:
                props["采集时间"] = {"text": ct}
            for name, val in list(zip(PROMO_NUM, r[3:]))[:len(PROMO_NUM)]:
                nv = norm_num(val)
                if nv is not None:
                    props[name] = {"number": nv}
            promo_rows.append((key, props))

    # 商品数据
    ws2 = wb["商品数据"]
    prod_rows, seen_prod = [], set()
    for r in list(ws2.iter_rows(values_only=True))[1:]:
        if not r or not r[0]:
            continue
        d = norm_date(r[0])
        acct = norm_text(r[2])
        pid = norm_text(r[4])
        if not d or not acct:
            continue
        key = acct + "|" + d + "|" + pid
        if key in seen_prod:
            continue
        seen_prod.add(key)
        props = {"数据日期": {"date": d}, "账号": {"text": acct}}
        ct = norm_text(r[1])
        if ct:
            props["采集时间"] = {"text": ct}
        props["商品名称"] = {"text": norm_text(r[3])[:120]}
        if pid:
            props["商品ID"] = {"text": pid}
        for name, val in list(zip(PROD_NUM, r[5:]))[:len(PROD_NUM)]:
            nv = norm_num(val)
            if nv is not None:
                props[name] = {"number": nv}
        prod_rows.append((key, props))

    ops_exist = existing_keys(OPS_DB, ["账号", "数据日期"])
    prod_exist = existing_keys(PROD_DB, ["账号", "数据日期", "商品ID"])
    promo_exist = existing_keys(PROMO_DB, ["账号", "数据日期"])

    ops_new = [p for k, p in ops_rows if k not in ops_exist]
    prod_new = [p for k, p in prod_rows if k not in prod_exist]
    promo_new = [p for k, p in promo_rows if k not in promo_exist]

    ops_added = prod_added = promo_added = 0
    if not DRY:
        if ops_new:
            ops_added = add_records(OPS_DB, ops_new)
        if prod_new:
            prod_added = add_records(PROD_DB, prod_new)
        if promo_new:
            promo_added = add_records(PROMO_DB, promo_new)

    summary = {
        "source": source,
        "requests": {"pending_found": len(reqs),
                     "closed": close_requests(reqs, "已完成",
                                              "运营+%d 商品+%d 推广+%d" % (len(ops_new), len(prod_new), len(promo_new)))
                               if not DRY else 0},
        "ops": {"xlsx_rows": len(ops_rows), "db_before": len(ops_exist),
                "new_rows": len(ops_new), "added": ops_added},
        "prod": {"xlsx_rows": len(prod_rows), "db_before": len(prod_exist),
                 "new_rows": len(prod_new), "added": prod_added},
        "promo": {"xlsx_rows": len(promo_rows), "db_before": len(promo_exist),
                  "new_rows": len(promo_new), "added": promo_added},
        "dry_run": DRY,
        "errors": errors,
        "ok": True,
    }
    io.open(os.path.join(BASE, "data", "sync2_result.json"), "w", encoding="utf-8").write(
        json.dumps(summary, ensure_ascii=False, indent=2))
    print("SYNC2_OK " + json.dumps(summary, ensure_ascii=False))
    # 签名 URL 30 分钟有效，用后删除防止下次误用
    try:
        os.remove(URL_FILE)
    except OSError:
        pass


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        try:
            pending = pending_requests()
            close_requests(pending, "失败", str(e)[:120])
        except Exception:
            pass
        print("SYNC2_FAIL %r" % (e,))

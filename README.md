# 账号运营分析台 · 项目交付说明

## 一、在线工作台（交付主体）

- 访问链接：https://www.workbuddy.cn/space/d/dlo1FFkVU38ECnz52MKXwX
- 资料库节点：`dlo1FFkVU38ECnz52MKXwX`（kind=web，协作态；点页面右上角「发布」可对外公开）
- 本地源码：`delivery/account-workbench.html`（单文件，CSS/JS 全内联，图表为手写 SVG，无外部依赖）

### 页面 4 个模块
1. **今日要处理 + 核心指标**：12 张 KPI 卡（含环比）+ 自动预警（有流量无成交、响应率不达标、GMV 腰斩、零动销、推广有花费无成交、投产比<3 等），可一键标记处理
2. **账号 / 商品 / 推广 三 Tab**：
   - 账号维度：各账号曝光/访问/浏览/询单/支付/客单价/转化率对比表（可排序、带合计行）
   - 商品维度：商品指标卡 + 商品明细表 + TOP10 排行 + 各账号商品结构
   - 推广维度：推广指标卡 + 账号明细表（含 CPC/CPA/CPM）+ 投产比排行（ROI<3 标红）+ 推广漏斗
3. **趋势分析**：15 个指标切换（运营 8 + 推广 7），日 / 月 / 年三种粒度，点上有悬浮数值提示
4. **转化漏斗与诊断**：曝光→访问→浏览→询单→支付 五级漏斗 + 账号健康度评分 + 优化建议

### 交互能力
- 顶部「选择日期」按钮 + 三个模块旁日期标签均可点击，弹出统一选择器：按日/月/年 × 单周期/区间，含「最近 7/14/30 天、全部数据」快捷项；应用后全页联动（环比自动取等长上一区间）
- 「同步腾讯文档」按钮：往《同步请求》表写一条待处理，自动化执行后回写结果，页面通过数据订阅自动刷新
- 「刷新」重新拉取数据表；「导出快照」下载 JSON 备份

## 二、数据源与数据表

| 环节 | 标识 |
|---|---|
| 腾讯文档 | 《运营/商品/推广数据》 file_id `DWkhnWXZvc1FSVWVk`，URL https://docs.qq.com/sheet/DWkhnWXZvc1FSVWVk |
| 子表 | 运营数据 `BB08J2`(22列) / 商品数据 `9SNQRt`(21列) / 推广数据(23列) |
| 运营表 | 《账号每日运营数据》`Sy50vzHB3nutPgCov3jQZs`（主键 账号+数据日期） |
| 商品表 | 《商品数据》`z6wRbDAhPSaJ9D5bYOYIOk`（主键 账号+数据日期+商品ID） |
| 推广表 | 《推广数据》`jNNOmZBBXGRNGK194W8gV9`（主键 账号+数据日期） |
| 请求表 | 《同步请求》`1y8ejlIduZbq4WY3uad8DR`（字段 请求时间/状态/结果/来源） |

四张表均挂在资料库「我的文档」同一目录下（与源文档同级）。

## 三、目录结构

```
D:\workbuddy\2026-09-18-22-20-37\delivery\
├── README.md                  本说明
├── account-workbench.html     工作台源码（线上同版）
├── scripts\                   全部脚本
│   ├── sync_tdoc2.py          三表同步入口（MCP 导出 → 解析 → 去重追加）
│   ├── tdoc_mcp.py            腾讯文档 MCP 直连工具（读数据唯一通道）
│   ├── lib.py                 资料库官方脚本驱动（绕过 PowerShell 编码错位）
│   ├── step_import.py         页面重导入（覆盖原节点、链接不变）
│   ├── create_prod_db.py      建商品数据表
│   ├── create_promo_db.py     建推广数据表
│   ├── create_req_db.py       建同步请求表
│   ├── upgrade_ops_db.py      运营表改名+加字段
│   ├── repair_pct.py          比率字段量纲巡检修复
│   ├── export_tdoc.py / export_tdoc2.py   腾讯文档导出（旧/新文档）
│   └── probe_*.py / gen_data.py / dump.py / run_skill.py / sync_xlsx_to_db.py   早期探测与建库脚本
├── test\
│   └── smoke.js               Node 最小 DOM 桩冒烟测试（渲染/日期联动/商品/推广/悬浮提示）
├── data\                      运行产物：同步结果、表结构、argv、日志、临时 xlsx
└── samples\
    └── source_tdoc_2026-09-26.xlsx   源文档导出样例
```

## 四、常用命令

```powershell
# 1) 取资料库票据（在 WorkBuddy 会话内通过 connect_open_platform 获得，勿落盘）
# 2) 手动同步一次（三表，按主键去重，只追加）
$env:PYTHONIOENCODING='utf-8'
"<token>" | & "C:\Users\张彦飞\.workbuddy\binaries\python\versions\3.13.12\python.exe" `
  "D:\workbuddy\2026-09-18-22-20-37\delivery\scripts\sync_tdoc2.py"          # 加 --dry-run 只试算

# 3) 改完页面后重新导入（链接不变）
"<token>" | & "...\python.exe" "D:\workbuddy\2026-09-18-22-20-37\delivery\scripts\step_import.py"

# 4) 冒烟测试
& "C:\Users\张彦飞\.workbuddy\binaries\node\versions\22.12.0\node.exe" `
  "D:\workbuddy\2026-09-18-22-20-37\delivery\test\smoke.js"                   # 末尾输出 SMOKE_OK
```

## 五、自动化

- 名称：账号运营+商品数据同步（含网页触发），id `b09c3365-3e8f-45f7-8b0d-9f3ad50445aa`
- 频率：每小时一次（RRULE `FREQ=HOURLY;INTERVAL=1`）
- 行为：先查《同步请求》待处理 → 执行三表增量同步 → 回写请求结果为已完成/失败

## 六、注意事项（踩过的坑）

1. **腾讯文档只能这样读**：开放平台 API 只写不读；官方 CLI 报 502；可用路径是 `tdoc_mcp.py` 直连 `https://docs.qq.com/openapi/mcp`（票据从本地网关 `/internal/tencent-docs/tokens` 取，须整组透传 Authorization + X-WorkBuddy-MCP-Context 且不走代理）。
2. **PowerShell 传含中文的命令行参数会按 GBK 编码、Python 按 UTF-8 解码 → JSON 损坏**：一律用 `lib.py` 驱动（argv 来自 UTF-8 文件、token 走 stdin）。
3. **Node 读中文文件名路径会 ENOENT**：产物文件一律用 ASCII 名（故页面源码文件名为 `account-workbench.html`）。
4. **Git Bash heredoc 会把脚本里的 `\` 变成 `/`**：写含反斜杠的脚本用 Write 工具落盘，不要在 heredoc 里拼 Windows 路径。
5. **资料库 SDK 变量必须命名为 `db`**，且 `databaseId` 要用字符串字面量，否则页面 lint（DSDK002/DSDK007/DSDK011）不通过。
6. 页面发布后链接公开可访问，不要把腾讯文档票据等敏感信息写进 HTML。

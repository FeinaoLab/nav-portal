# -*- coding: utf-8 -*-
"""从线上拉取 25 个手机端 PWA 的 manifest，生成 apps.py 数据源。

手机端统一部署在 /<prefix>/m/，每个都带 manifest.webmanifest（name / short_name /
description / theme_color / icon）。这个脚本把这些元信息抓下来，导航页就能像应用商店
那样陈列它们。服务器没加新 APP 就不用重跑；加了新的先跑本脚本再跑 build_nav.py。

    python fetch_apps.py
"""
import io
import json
import os
import sys
import urllib.request
from concurrent.futures import ThreadPoolExecutor

HOST = "http://42.193.158.63"

# (前缀, 备用名称) —— 顺序即页面上的顺序，按分组排
PREFIXES = [
    # 平台
    ("dmp", "飞舞数据中台手机端"),
    # 研发与知识
    ("okr", "飞绩绩效手机端"),
    ("lms", "飞学学习手机端"),
    ("kms", "飞知知识手机端"),
    ("edu", "飞育教育手机端"),
    # 企业运营
    ("erp", "飞鸢ERP手机端"),
    ("fin", "飞云财务手机端"),
    ("finan", "飞融金融手机端"),
    ("cost", "飞奔成本手机端"),
    ("tax", "飞税税务手机端"),
    ("hr", "飞花HRM手机端"),
    ("oa", "飞效OA手机端"),
    ("flow", "飞流流程手机端"),
    ("aps", "飞划APS手机端"),
    ("tms", "飞运运输手机端"),
    ("ocean", "飞洋海运手机端"),
    ("cus", "飞扬关务手机端"),
    ("retail", "飞售零售手机端"),
    ("rms", "飞餐餐饮手机端"),
    ("his", "飞医医疗手机端"),
    ("pu", "飞瀑能源手机端"),
    ("fh", "飞虹股票手机端"),
    ("qms", "飞控QMS手机端"),
    ("wms", "飞传WMS手机端"),
    ("mes", "飞驰MES手机端"),
    ("scm", "飞泉SCM手机端"),
    ("crm", "飞鹰CRM手机端"),
]


def fetch(item):
    prefix, fallback = item
    base = "%s/%s/m/" % (HOST, prefix)
    url = base + "manifest.webmanifest"
    try:
        with urllib.request.urlopen(url, timeout=8) as r:
            m = json.loads(r.read().decode("utf-8"))
    except Exception as e:
        return {
            "prefix": prefix, "name": fallback, "short": fallback[:4],
            "desc": "", "theme": "#64748b", "icon": base + "icon.svg",
            "landing": base, "down": True, "err": str(e)[:60],
        }

    icons = m.get("icons") or []
    icon = base + "icon.svg"
    for ic in icons:
        src = ic.get("src", "")
        if not src:
            continue
        icon = src if src.startswith("http") else base + src.lstrip("./")
        if "svg" in (ic.get("type") or "") or src.endswith(".svg"):
            break

    return {
        "prefix": prefix,
        "name": m.get("name") or fallback,
        "short": m.get("short_name") or (m.get("name") or fallback)[:5],
        "desc": m.get("description") or "",
        "theme": m.get("theme_color") or "#2f6fed",
        "bg": m.get("background_color") or "#0f172a",
        "icon": icon,
        "landing": base,
        "down": True,
        "err": "",
    }


def main():
    with ThreadPoolExecutor(max_workers=10) as ex:
        apps = list(ex.map(fetch, PREFIXES))

    ok = [a for a in apps if not a["err"]]
    bad = [a for a in apps if a["err"]]

    lines = [
        "# -*- coding: utf-8 -*-",
        '"""手机 APP 登记表 —— 由 fetch_apps.py 自动生成，别手改。"""',
        "",
        "# prefix: 对外路径前缀，手机端地址 = /<prefix>/m/",
        "# name / short / desc / theme / icon 全部取自各 APP 自己的 manifest.webmanifest",
        "APPS = [",
    ]
    for a in apps:
        lines.append("    {")
        lines.append('        "prefix": %r, "name": %r, "short": %r,' % (a["prefix"], a["name"], a["short"]))
        lines.append('        "desc": %r, "theme": %r, "bg": %r,' % (a["desc"], a["theme"], a["bg"]))
        lines.append('        "icon": %r, "landing": %r,' % (a["icon"], a["landing"]))
        lines.append("    },")
    lines.append("]")
    lines.append("")

    out = os.path.join(os.path.dirname(os.path.abspath(__file__)), "apps.py")
    io.open(out, "w", encoding="utf-8", newline="\n").write("\n".join(lines))
    print("生成:", out, "| 可用", len(ok), "| 失败", len(bad))
    for b in bad:
        print("  失败:", b["prefix"], b["err"])


if __name__ == "__main__":
    main()

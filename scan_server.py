#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""扫描云服务器上所有已部署系统：对外路径、端口、名称、探活状态、systemd 单元。"""
import json
import os
import re
import subprocess
import urllib.request
import urllib.error

NGINX = "/etc/nginx/conf.d/wanqian-kb.conf"
UNIT_DIR = "/etc/systemd/system"
HOST = "42.193.158.63"


def parse_nginx():
    s = open(NGINX, encoding="utf-8").read()
    out = {}
    for m in re.finditer(r"location\s+(=)?\s*(/[^\s{]*)\s*\{([^}]*)\}", s):
        body = m.group(3)
        if "/m/" in m.group(2) or m.group(1) or m.group(2) in ("/", "/index.html"):
            continue
        if m.group(2) in ("/api/", "/api/ai/", "/files/"):
            continue
        pm = re.search(r"proxy_pass\s+http://127\.0\.0\.1:(\d+)", body)
        am = re.search(r"alias\s+(\S+?)/?;", body)
        out[m.group(2)] = {
            "path": m.group(2),
            "port": int(pm.group(1)) if pm else None,
            "alias": am.group(1) if am else None,
        }
    return out


def units():
    """unit 名 -> (description, working_dir, exec)"""
    res = {}
    for fn in os.listdir(UNIT_DIR):
        if not fn.endswith(".service"):
            continue
        name = fn[:-8]
        try:
            txt = open(os.path.join(UNIT_DIR, fn), encoding="utf-8").read()
        except Exception:
            continue
        desc = re.search(r"^Description=(.*)$", txt, re.M)
        wd = re.search(r"^WorkingDirectory=(.*)$", txt, re.M)
        ex = re.search(r"^ExecStart=(.*)$", txt, re.M)
        res[name] = {
            "desc": desc.group(1).strip() if desc else "",
            "wd": wd.group(1).strip() if wd else "",
            "exec": ex.group(1).strip() if ex else "",
        }
    return res


def unit_of_port(port, us):
    """按 ExecStart / WorkingDirectory 里的端口或 spec.json 反查 unit"""
    hits = []
    for name, info in us.items():
        blob = info["exec"] + " " + info["wd"]
        if re.search(r":%d\b" % port, blob) or ("port=%d" % port) in blob or ("PORT=%d" % port) in blob:
            hits.append(name)
            continue
        # 通过 spec.json 里声明的 port 反查
        spec = None
        for cand in ("backend/spec.json", "spec.json", "app/spec.json"):
            p = os.path.join(info["wd"], cand) if info["wd"] else ""
            if p and os.path.exists(p):
                spec = p
                break
        if spec:
            try:
                d = json.load(open(spec, encoding="utf-8"))
                if d.get("port") == port:
                    hits.append(name)
            except Exception:
                pass
    return hits[0] if hits else None


def probe(path, port):
    """优先经 nginx 对外路径探活，失败再看直连端口"""
    for url in ("http://127.0.0.1" + path, "http://127.0.0.1:%d/" % port if port else None):
        if not url:
            continue
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 nav-scan"})
            r = urllib.request.urlopen(req, timeout=8)
            body = r.read(120000).decode("utf-8", "replace")
            t = re.search(r"<title[^>]*>(.*?)</title>", body, re.S | re.I)
            title = re.sub(r"\s+", " ", t.group(1)).strip() if t else ""
            return {"code": r.status, "title": title, "via": url}
        except urllib.error.HTTPError as e:
            try:
                body = e.read(60000).decode("utf-8", "replace")
                t = re.search(r"<title[^>]*>(.*?)</title>", body, re.S | re.I)
                title = re.sub(r"\s+", " ", t.group(1)).strip() if t else ""
            except Exception:
                title = ""
            return {"code": e.code, "title": title, "via": url}
        except Exception:
            continue
    return {"code": 0, "title": "", "via": None}


def main():
    biz = parse_nginx()
    us = units()
    rows = []
    for path, info in sorted(biz.items()):
        pr = probe(path, info["port"])
        unit = unit_of_port(info["port"], us) if info["port"] else None
        rows.append({
            "path": path,
            "port": info["port"],
            "code": pr["code"],
            "title": pr["title"],
            "unit": unit,
            "unit_desc": us.get(unit, {}).get("desc", "") if unit else "",
        })
    # 万千知识库本体
    pr = probe("/", None)
    rows.insert(0, {
        "path": "/", "port": 8080, "code": pr["code"], "title": pr["title"],
        "unit": "wanqian-kb", "unit_desc": us.get("wanqian-kb", {}).get("desc", ""),
    })
    print(json.dumps(rows, ensure_ascii=False, indent=1))


if __name__ == "__main__":
    main()

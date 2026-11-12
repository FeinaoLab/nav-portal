# 系统导航页

云服务器 `42.193.158.63` 上全部已部署系统的统一入口，外加一套手机 APP 的下载/安装入口。

- 线上地址：**http://42.193.158.63/nav/**
- 万千知识库首页底部有文字入口（`PortalHome.vue` 的 footer 链接行）

## 解决什么问题

服务器上分散着 55 个系统，路径是 `/pm/` `/fy/` `/erp/` 这类缩写，没人记得住；另外还有 27 个手机端，地址是 `/<前缀>/m/`，更没人记得。这个页面把入口、端口、用途、在线状态摊在一页里，支持搜索，手机上也排得下。

## 目录

| 文件 | 作用 |
|---|---|
| `registry.py` | **系统数据源**。分组、名称、路径、端口、一句话定位 |
| `apps.py` | **手机 APP 数据源**，由 `fetch_apps.py` 自动生成，别手改 |
| `fetch_apps.py` | 从线上抓 27 个 `/m/` 站点的 `manifest.webmanifest`，生成 `apps.py` |
| `build_nav.py` | 读上面两个数据源渲染出 `index.html`（单文件，CSS/JS 全内联，零外部依赖） |
| `index.html` | 构建产物，传到服务器 `/opt/nav/` |
| `scan_server.py` | 上服务器跑，扫实际部署情况（nginx location + systemd + 探活抓 title） |
| `deploy.sh` | 一键部署：生成 → 打包 → scp → 远端解包 → 校验 |
| `preview-desktop.png` / `preview-mobile.png` / `preview-install.png` | 线上实拍（含安装引导弹层，82 项全绿） |
| `preview-kb-footer.png` | 万千知识库首页页脚，只有一行文字入口 |

## 手机 APP 怎么体现的

手机端是 PWA，不是 APK。所以页面上没有「下载安装包」，做的是两件事：

1. **陈列**：每个 APP 一张卡，图标、短名、系统全名，图标和主题色直接取自该 APP 自己的 manifest，改了那边的 manifest，这边重新抓一次就同步。
2. **引导安装**：点卡片底部的「安装」，弹出分平台步骤（安卓 / iPhone / 电脑），按 UA 自动选中当前设备对应的那个 tab。弹层里还有「直接打开」和「复制链接」。

几个刻意的设计：

- **微信内打开会额外提示**。微信内置浏览器装不了 PWA，弹层里直接给出「点右上角 … → 在浏览器打开」的出路，省得人卡在那。
- **电脑 tab 是真实路径**。Chrome / Edge 打开 `/xxx/m/`，地址栏就会出现安装图标，装完是独立窗口，不是浏览器标签。
- **没有伪造「一键安装」按钮**。跨文档抓不到目标站点的 `beforeinstallprompt`，所以老老实实给步骤 + 跳转，不做点了没反应的假按钮。

手机上这个区块排在系统列表最前面，因为手机访客打开导航页，第一需求通常是「装个 APP 到桌面」。

## 新增系统 / 新增 APP 后怎么更新

系统（桌面端）：

1. `registry.py` 对应分组加一行：
   ```python
   ("CODE", "系统名称", "/path/", 端口号, "一句话说清它干什么", "标签"),
   ```
   标签可留空；`主力` `核心` `AI` `API` `本站` 会显示成小徽章。

手机端：

1. `fetch_apps.py` 的 `PREFIXES` 里加前缀（顺序即页面顺序）
2. `python fetch_apps.py`

然后一条命令部署：

```bash
bash deploy.sh              # 只推导航页
bash deploy.sh --with-kb    # 连万千知识库前端一起推
```

脚本做的事：`build_nav.py` 重新生成 → tar 打包 → scp 到 `/tmp` → 远端解到 `/opt/nav/`；
带 `--with-kb` 时，知识库前端先解到 `/opt/kb/dist.new` 再整体切换，避免解压中途页面 404。最后自己 curl 校验状态码和 APP 卡片数。

> 服务器只吃 `/opt/nav/index.html` 这一个文件，改完必须跑一次，否则线上还是旧的。

## 想重新扫一遍服务器

不确定现在到底部署了什么，跑这个：

```bash
scp -i ~/.ssh/wanqian_deploy scan_server.py root@42.193.158.63:/tmp/
ssh -i ~/.ssh/wanqian_deploy root@42.193.158.63 "cd /tmp && python3 scan_server.py > /tmp/nav_scan.json"
scp -i ~/.ssh/wanqian_deploy root@42.193.158.63:/tmp/nav_scan.json .
```

输出每条包含：对外路径、内网端口、HTTP 状态、页面 title、systemd 单元名与描述。只读配置、只发 GET，不改任何东西。

## nginx 配置

写在 `/etc/nginx/conf.d/wanqian-kb.conf` 的 `location / {` 之前：

```nginx
location = /nav { return 301 /nav/; }
location /nav/ {
    root /opt;
    try_files $uri $uri/index.html =404;
}
```

> 别用 `alias /opt/nav/;` + `index index.html;`。实测 `/nav/` 会渲染出知识库首页，因为 alias 和 index 的内部重定向会串到 `location /`。`root /opt` + `try_files` 才稳。

改完 `nginx -t && systemctl reload nginx`，配置改动前先备份到 `/root/wanqian-kb.conf.bak-<时间>`。

## 状态点怎么来的

打开页面时前端对每个路径发起同源 `fetch`（并发上限 6，单个 6 秒超时）：

- 绿点：HTTP 2xx / 3xx
- 黄点：有响应但非 200（通常是要求登录）
- 红点：无响应或 5xx

右上角「重新检测」重跑一遍。只发 GET，不带凭据。

## 截图的正确姿势

Windows 上 Chrome 无头加 `--window-size=390,...` 会把视口撑到 660 左右（受系统显示缩放影响），媒体查询不生效、右侧被裁。别用 Chrome 截图，用 playwright 显式设视口：

```bash
playwright-cli open
playwright-cli resize 390 844
playwright-cli goto "http://127.0.0.1:8899/index.html"
playwright-cli screenshot --filename=preview-mobile.png --full-page
```

注意 playwright-cli 的会话不跨命令调用，四条要写在同一次 shell 执行里。

## 当前统计（2026-11-12）

| 分组 | 数量 |
|---|---|
| 手机 APP | 27 |
| 平台与基础设施 | 5 |
| 研发与知识 | 6 |
| 企业运营 | 29 |
| 电商矩阵 | 12 |
| AI 能力服务（纯 API） | 3 |
| **合计** | **82**（55 系统 + 27 APP） |

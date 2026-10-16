# Windows 完整便携版

下载 GitHub Releases 中的 sci-browser-1.0.0-windows-x64.zip，完整解压到可写目录，双击 sci-browser.exe。

包含 Chromium 154.0.8037.58、Mihomo 1.19.30、Python 3.12、Playwright 及项目维护源码。无需另装 Python，也不要仅复制 sci-browser.exe；它依赖同目录的 runtime、extensions、services。

首次启动自动生成随机本机令牌和空白配置，默认直连。在 sci-proxy → 选项中填写自己的 SOCKS5 节点后再启用代理。浏览器资料保存在解压目录 profiles，升级时请先备份自己的本地配置和资料。

需要 Windows x64 与 .NET Framework 4.x。便携包未使用代码签名证书；发布页提供 SHA256SUMS.txt 供核对。

统一 Playwright 入口仍为 scripts/playwright-会话自动化-v1.ps1；完整包使用 runtime/python，不依赖系统 Python。源码构建用户仍可使用原 Python 3.12 虚拟环境方式。

本地管理端口 17896、代理端口 17895 固定；不要并行运行不同副本。若已有旧服务占用端口，应先结束旧副本的本地代理服务再启动新副本。

项目维护源码位于 Git 仓库和发布附件 sci-browser-1.0.0-source.zip。Mihomo 对应版本源码另附 mihomo-source-v1.19.30.zip；Chromium 的完整内核源码不在本仓库，相关上游许可及浏览器内置 credits 保留在 docs/third-party 与运行文件中。本发布未声称可从当前仓库重建定制 Chromium 内核。

## 完整便携包验证

便携 Python 的 ssl、sqlite3、Playwright 和项目模块加载通过；通过独立临时端口验证实际本地认证 API；实际启动包内 Chromium 并加载 sci-proxy 与 sci-cookie。启动器 --check 首次初始化成功，重复运行保留随机令牌，初始节点为空且代理关闭。测试没有关闭或修改用户正在运行的代理服务。

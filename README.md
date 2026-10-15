# sci-browser

基于现有 Chromium 运行文件的 Windows 浏览器启动器与扩展工具，维护者 LavineLeo。

此目录是独立整理的 GitHub 源码版本，包含本项目的启动器、代理扩展、Cookie 工具、论文下载适配和本地服务。**不包含完整 Chromium 内核源码，也不包含浏览器运行二进制。** 原工作目录不受影响。

## 功能与目录

| 目录 | 内容 |
| --- | --- |
| src/launcher/app | C# 启动器入口 |
| src/launcher/core | 浏览器定位、启动参数和本地服务管理 |
| extensions/sci-proxy | 19.0.0：代理菜单、节点设置、网站连接记忆和直连规则显示 |
| extensions/web-cookie-skill | Cookie 工具及 sci-cookie 扩展 |
| extensions/browser-paper-download | 上游论文下载项目与 Windows 适配 |
| services/mihomo/bridge | 本地认证 API、节点应用、出口探测 |
| assets/icons | 浏览器品牌图标 |
| scripts | 当前构建、配置初始化与工具入口 |
| docs | 架构、依赖与发布边界 |
| plans | 版本化整理计划 |

## Windows 首次配置

需要 Python 3.12、Windows PowerShell 和 .NET Framework 4.x C# 编译器。

1. 准备浏览器完整运行目录，放入 `runtime/Chrome-bin-v4/`，其中必须有 `chrome.exe` 及全部相邻资源。当前已验证的是原项目使用的定制 Chromium 运行目录；其他浏览器可能不支持相同的扩展加载参数。
2. 将兼容的 Mihomo 内核放入 `services/mihomo/core/mihomo.exe`。
3. 在此目录执行：

```powershell
py -3.12 scripts/setup-本地配置-v1.py
powershell -NoProfile -ExecutionPolicy Bypass -File scripts/build-启动器构建-v6.ps1
.\sci-browser.exe
```

初始化会随机生成本机认证令牌，首次默认关闭代理，不携带任何预置节点。打开 sci-proxy → 选项，填写自己的真实 SOCKS5 节点，保存后再开启代理。重复初始化保留现有令牌和节点状态；移动目录后应先关闭本目录的浏览器及配套服务，再重新初始化以更新内核路径。

本地 API 使用 127.0.0.1:17896，代理出口为 127.0.0.1:17895。不要同时启动多个配置不同的副本；若旧项目已占用端口，新副本会提示冲突。

## 可选 Python 工具

内置 sci-cookie 扩展无需 Python 依赖。Cookie 命令行工具与论文下载适配分别安装：

```powershell
py -3.12 -m venv extensions/web-cookie-skill/venv-3.12
& extensions/web-cookie-skill/venv-3.12/Scripts/python.exe -m pip install -r extensions/web-cookie-skill/requirements/requirements.txt
py -3.12 -m venv extensions/browser-paper-download/venv-3.12
& extensions/browser-paper-download/venv-3.12/Scripts/python.exe -m pip install -r extensions/browser-paper-download/windows/requirements.txt
```

论文下载首次使用 `scripts/papers-论文下载-v1.ps1 setup` 打开独立持久登录窗口；随后使用 `download --queue queue.json --dest papers`。登录状态不会自动继承日常浏览器。Cookie 命令行帮助：`scripts/cookies-工具入口-v1.ps1 --help`。上游详细说明位于各扩展目录。

## GitHub 发布范围

此目录没有复制账号密码、代理节点、本地认证令牌、Cookie、个人浏览器资料、虚拟环境、下载论文、CRX 或私钥。初始化产生的配置由 .gitignore 排除。历史脚本与旧 UI 文件未带入，仅保留当前引用链所需文件。

尚未创建远程仓库或上传 GitHub。浏览器及 Mihomo 二进制需要另行准备；若未来发布二进制，需保留其上游许可证及源码提供义务，见 [第三方说明](docs/第三方与运行依赖.md)。本仓库尚未给项目自有代码指定统一开源许可证。

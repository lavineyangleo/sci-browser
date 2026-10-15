# sci-cookie 与 web-cookie-skill

## 在 sci-browser 中获取当前网页 Cookie

1. 完全关闭 sci-browser 的所有窗口，再双击项目根目录 `sci-browser.exe`，让新增扩展加载。
2. 访问目标网站并完成需要的登录。
3. 在右上角扩展菜单打开 **sci-cookie**，点击“读取 Cookie”。
4. 列表默认脱敏，可选择显示完整值，或点击“导出 JSON”保存到本地。

读取包含 HttpOnly Cookie，按当前 URL 的域名、路径与 Cookie 存储区筛选。不是读取全部网站的 Cookie。浏览器内页不能读取；没有 Cookie 的网页会显示 0 条。

“每 5 秒刷新”仅在面板打开期间工作，不会后台持续收集或自动导出。扩展不上传 Cookie，也不修改网站 Cookie。JSON 使用原工具 schemaVersion 1.0，可交给原 validate.py 校验。

## Python 命令行入口

环境：`extensions/web-cookie-skill/venv-3.12`，已安装 Playwright。复用项目内 Chromium，无需另下载浏览器。

在项目根目录执行：

```powershell
.\scripts\cookies-工具入口-v1.ps1 scan --url "https://目标网站/" --headed
.\scripts\cookies-工具入口-v1.ps1 save --url "https://目标网站/" --output "cookies/site.json" --headed
.\scripts\cookies-工具入口-v1.ps1 sync "cookies/site.json" --dry-run
.\scripts\cookies-工具入口-v1.ps1 watch "cookies/site.json" --interval 10
```

命令行使用工具自己的 `.cookie-profile`，不会自动拥有 sci-browser 的登录态。获取正在使用的浏览器登录态，请使用内置 sci-cookie。不要让命令行和浏览器同时占用同一用户目录。

## 验证结果

在独立测试浏览器访问真实 Google 网页后，读取到 4 条 Cookie，其中 2 条 HttpOnly；快照通过原 cookie_core.validate_snapshot 检查。输出只记录数量，不记录完整 Cookie 值。无效浏览器内页被拒绝，旧结果和导出状态会清空。
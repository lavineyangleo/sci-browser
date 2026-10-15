# web-cookie-skill

精简版网页 Cookie Skill，只做四个动作：

- `scan`：识别网页 Cookie。
- `save`：保存为 JSON snapshot。
- `sync`：按浏览器当前状态更新 snapshot。
- `watch`：持续轮询并自动更新 snapshot。

```bash
pip install -r requirements/requirements.txt
playwright install chromium

python scripts/cookie_tool.py scan --url https://example.com
python scripts/cookie_tool.py save --url https://example.com --output cookies/example.json
python scripts/cookie_tool.py sync cookies/example.json --dry-run
python scripts/cookie_tool.py watch cookies/example.json --interval 10
```

需要登录态时，给命令传同一个 `--user-data-dir .cookie-profile`。

Cookie value 默认不完整显示；snapshot 是敏感文件，不应提交版本控制。

本实现仅参考 EditThisCookie 的功能目标，未移植其扩展 UI 或源码；实现重点是 Cookie 读取、持久化和同步。

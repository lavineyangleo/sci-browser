---
name: web-cookie-skill
description: |
  本 Skill 用于识别网页 Cookie、将 Cookie 保存为本地 JSON 快照，并让已保存快照按浏览器当前状态自动更新。
  当用户需要读取网页 Cookie、保存 Cookie、同步 Cookie 或持续跟踪 Cookie 变化时触发。
  触发词："识别cookie"、"读取cookie"、"保存cookie"、"同步cookie"、"更新cookie"
version: 1.0.0
author: Project Team
license: UNLICENSED
tags: [Cookie, Browser, Playwright]
dependencies: [playwright>=1.54,<2]
---

# 网页 Cookie 识别、保存与自更新

## Quick Start

本 Skill 只解决三件事：**识别 Cookie、保存 Cookie、自动更新 Cookie**。默认使用 Playwright Chromium BrowserContext，因此可以读取浏览器级 Cookie，包括 HttpOnly Cookie。Cookie value 默认脱敏显示，保存到 snapshot 时才保留完整值。

安装：

```bash
pip install -r requirements/requirements.txt
playwright install chromium
```

最小用法：

```bash
python scripts/cookie_tool.py scan --url https://example.com
python scripts/cookie_tool.py save --url https://example.com --output cookies/example.json
python scripts/cookie_tool.py sync cookies/example.json
```

需要保留登录态时，为 Skill 使用独立 profile：

```bash
python scripts/cookie_tool.py save \
  --url https://example.com \
  --output cookies/example.json \
  --user-data-dir .cookie-profile
```

## 工作流程

### Workflow 1: 识别网页 Cookie

```text
任务进度：
- [ ] Step 1: 确认目标 URL
- [ ] Step 2: 读取 Cookie
- [ ] Step 3: 检查 Cookie 属性
- [ ] Step 4: 保持 value 脱敏
```

**Step 1-2: 扫描网页 Cookie**

```bash
python scripts/cookie_tool.py scan --url https://example.com
```

需要使用已有登录态：

```bash
python scripts/cookie_tool.py scan \
  --url https://example.com \
  --user-data-dir .cookie-profile
```

**Step 3: 识别属性**

重点读取：`name/domain/path/expires/httpOnly/secure/sameSite/session/partitionKey`。

**Step 4: 避免泄露**

默认不展示完整 value。只有任务明确需要时才使用 `--show-values`。

### Workflow 2: 保存 Cookie

```text
任务进度：
- [ ] Step 1: 扫描目标 URL
- [ ] Step 2: 保存 JSON snapshot
- [ ] Step 3: 验证 snapshot
- [ ] Step 4: 不提交 Cookie 文件到 Git
```

保存：

```bash
python scripts/cookie_tool.py save \
  --url https://example.com \
  --output cookies/example.json \
  --user-data-dir .cookie-profile
```

验证：

```bash
python scripts/validate.py cookies/example.json
# 如有错误：重新捕获或修复 → 再验证
```

Snapshot 结构见 [references/cookie-schema.md](references/cookie-schema.md)。

### Workflow 3: 自动更新 Cookie

```text
任务进度：
- [ ] Step 1: 读取旧 snapshot
- [ ] Step 2: 获取浏览器当前 Cookie
- [ ] Step 3: 比较 added/updated/removed
- [ ] Step 4: 原子更新 snapshot
```

先预览变化：

```bash
python scripts/cookie_tool.py sync cookies/example.json \
  --user-data-dir .cookie-profile \
  --dry-run
```

正式更新：

```bash
python scripts/cookie_tool.py sync cookies/example.json \
  --user-data-dir .cookie-profile
```

需要持续自更新时：

```bash
python scripts/cookie_tool.py watch cookies/example.json \
  --user-data-dir .cookie-profile \
  --interval 10
```

`watch` 保持浏览器上下文运行并轮询 Cookie；只在 Cookie 实际变化时更新 snapshot。

## 适用场景 vs 替代方案

**使用本 Skill 当：**
- 需要识别某网页当前 Cookie。
- 需要把 Cookie 登录态保存成文件。
- 需要让保存的 Cookie 文件跟随浏览器状态更新。

**使用浏览器扩展当：**
- 需要人工 UI 编辑 Cookie。
- 需要在 Chrome 扩展内部监听 `cookies.onChanged`。

## 常见问题

**问题：读取不到登录后的 Cookie**

使用同一个独立 profile：

```bash
python scripts/cookie_tool.py scan --url https://example.com --user-data-dir .cookie-profile
```

不要同时让多个 Chromium 进程占用同一个 profile。

**问题：不希望访问页面，只想读取 profile 里的已有 Cookie**

```bash
python scripts/cookie_tool.py scan \
  --url https://example.com \
  --user-data-dir .cookie-profile \
  --no-navigate
```

**问题：Cookie 文件包含敏感登录信息**

不要提交到 Git，不要把完整 snapshot 内容直接输出到聊天或日志。默认 `scan` 已对 value 脱敏。

## 进阶参考（按需查阅）

- Cookie snapshot 与 identity: [references/cookie-schema.md](references/cookie-schema.md)

## 资源链接

- Playwright BrowserContext Cookies: https://playwright.dev/docs/api/class-browsercontext
- EditThisCookie: https://github.com/ETCExtensions/Edit-This-Cookie

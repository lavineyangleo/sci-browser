# Playwright 自动化与 Cookie 环境关联

## sci-cookie 2.0

在真实网页上打开 sci-cookie，点击“读取 Cookie”。导出的 JSON 保留 schemaVersion 1.0 和原 cookies 字段，新增 environment、fingerprint、session、loginEvidence。

- environment：真实 User-Agent、平台、语言、时区、屏幕、像素比、CPU 线程数、可用的设备内存与 UA Client Hints 基础字段。
- fingerprint：上述已记录字段的 SHA-256 摘要，不是登录凭证，也不是网站全部指纹；非安全页面可能无法生成摘要。
- session.profileId：当前扩展配置目录的随机稳定标识，清空扩展存储或重新安装后可能改变。它与 Playwright 独立目录的标识不同，比较时会显示差异。
- loginEvidence：用户指定的 CSS 选择器对应的可见元素。仅出现已登录信号则 authenticated，仅出现未登录信号则 unauthenticated；无信号、两者冲突或选择器无效时 unknown。

展开“登录信号与环境比较”，填写目标网站实际的账户菜单和登录表单选择器。这些规则按来源（协议、域名、端口）保存在本机，下次打开继续使用。选择旧 JSON 只做环境比较，不向网站导入 Cookie。旧版没有环境字段的快照会显示“不能比较”。跨站编辑 URL 时可读 Cookie，但不将当前页面的环境关联到其他来源。

只读取 Cookie 不代表已登录；页面选择器也是观察信号，不能替代服务器最终的会话验证。不修改 Canvas、WebGL 或伪造设备特征。

## Playwright 统一入口

使用已配置的论文下载 Python 环境，命令入口为 scripts/playwright-会话自动化-v1.ps1。

```powershell
.\scripts\playwright-会话自动化-v1.ps1 --help
```

命令：

| 操作 | 用途 | 额外参数 |
| --- | --- | --- |
| open | 打开可见浏览器，手动登录或操作后回终端按回车保存退出 | --url |
| collect | 按 CSS 选择器导出页面文本与链接到本地 JSON | --url --selector --out |
| snapshot | 导出当前来源 Cookie、环境及登录信号 | --url --out |
| check | 检测登录信号，可与快照比较环境 | --url，可选 --baseline --out |
| download | 通过浏览器下载一个真实 PDF，检查文件头，不覆盖现有目标 | --url --out |

所有操作均支持 --profile 指定环境名，默认 default。会话保存在 profiles/automation/session-环境名；同名会话跨次运行保留 Cookie 和其他浏览器存储，不允许并发占用。它与日常浏览器 profile、原论文批量下载 profile 相互独立。

--proxy 指定代理地址会保存到该 profile，下次沿用；--proxy direct 改回直连。该独立环境不加载 sci-proxy 的网站规则；需要原代理出口时先启动 sci-browser 服务，再设置 --proxy http://127.0.0.1:17895。

snapshot/check 可传 --authenticated-selector 和 --unauthenticated-selector；未提供时登录状态为 unknown。--baseline 只读取旧快照作差异比较，不导入会话。check 的终端摘要不含 Cookie 值；snapshot 的输出文件含完整 Cookie，需要自行保管。

现有 scripts/papers-论文下载-v1.ps1 继续负责论文批量队列、PubMed 查询与重命名。当前统一 download 是单 PDF 下载，不替代已有批量入口。

## 使用范围

这次增加的是环境记录、差异识别和持久会话能力，不保证跨设备搬迁登录。需要真实登录账号的验证应由用户先执行 open 手动完成；实现没有用测试 Cookie 或模拟登录数据证明登录成功。

### Python 接口

可在项目根目录通过相同 Python 环境导入 `services.automation.browser.session`，在 `with session(Path.cwd(), '环境名') as (context, page, metadata)` 内直接使用 Playwright 的 page.goto、page.locator、page.click、page.fill 等操作。退出上下文会关闭浏览器并保留该目录的会话。若需不同的自动化流程，无需复制浏览器启动逻辑。

### 本次真实验证

GitHub 登录页通过密码输入框信号识别为 unauthenticated；同一 profile 重开后环境比较 matching；无选择器的 arXiv 页面返回 unknown。页面采集成功提取《Attention Is All You Need》的实际标题，浏览器下载该论文 PDF 成功（2,215,244 字节）。sci-cookie 真实页面采集与跨 profile 差异展示通过。未使用真实账号完成已登录状态的验收，需用户在目标站点配置实际信号后验证。

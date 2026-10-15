# Cookie Snapshot Schema

本 Skill 只保存一种 JSON snapshot，避免格式转换带来的额外复杂度。

```json
{
  "schemaVersion": "1.0",
  "sourceUrl": "https://example.com",
  "capturedAt": "2026-09-26T12:00:00Z",
  "cookies": [
    {
      "name": "session_id",
      "value": "...",
      "domain": ".example.com",
      "path": "/",
      "expires": null,
      "httpOnly": true,
      "secure": true,
      "sameSite": "Lax",
      "session": true,
      "partitionKey": null
    }
  ]
}
```

Cookie identity 使用 `(name, domain, path, partitionKey)`。同名但不同 domain、path 或 partition 的 Cookie 是不同对象。

`sync` 比较旧 snapshot 和浏览器当前 Cookie：

- 新 identity：`added`
- 消失的 identity：`removed`
- identity 相同但属性或 value 改变：`updated`
- 完全一致：`unchanged`

Cookie value 属于敏感信息。`scan` 默认只显示掩码；snapshot 文件保存完整值，并在 POSIX 系统上尽量以 `0600` 权限写入。

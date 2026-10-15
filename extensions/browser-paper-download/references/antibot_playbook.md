# Anti-bot playbook (computer-use on Chrome)

All interactions go through computer-use against the user's real Chrome window.
Get fresh state with `get_app_state` (include_screenshot=true) before each click —
element indices and Turnstile positions shift between loads.

Tool names below (`get_app_state`, `left_click`, `zoom`, `mouse_move`,
`left_mouse_down`/`left_mouse_up`, `open_application`) are ZCode's computer-use
MCP. In other harnesses (Claude Code, Codex + any computer-use MCP, …) use the
equivalents: observe the accessibility tree, click elements or raster
coordinates, crop-zoom small targets. The browser must be the user's real
Chrome with their cookies — a headless/fresh-profile browser has no access.

## General rules

- Chrome must be **frontmost** for raw event clicks (`strategy="event"`); activate via
  `open_application(activate=true)` first. AXPress on links works in background too and
  commonly reports `target_verification_status: mismatched` **while still working** —
  verify by effect (tab URL/title/download), not by the receipt.
- Chrome settings pages (chrome://settings/...) ignore both AXPress and event clicks on
  web-radio elements; click the row LABEL text with `strategy="event"`, then re-observe.
- Keep a `caffeinate` running for long batches; display sleep breaks screencapture
  (`could not create image from display`) and can strand the Chrome window on another
  Space. Fix a stranded window by quitting + reopening Chrome (cookies survive).
- One challenge pass per **domain** sets the cf_clearance cookie; batch the whole domain
  right after passing. Subdomains count as separate domains (onlinelibrary.wiley.com vs
  acrjournals.onlinelibrary.wiley.com).

## Cloudflare Turnstile ("正在安全验证 / 请验证您是真人 / Just a moment...")

1. `get_app_state` (screenshot). The widget is usually exposed as
   `checkbox 请验证您是真人 = 0`.
2. Try `left_click` on the element. Then `zoom` on the widget region to check the
   checkmark. AXPress often silently fails — if still unchecked:
3. `mouse_move` to the checkbox raster coords, then `left_mouse_down` + `left_mouse_up`
   (a human-paced click). Typical coords at default window size: the small square at
   ~(243, 402); ScienceDirect asset-gate page: ~(152, 331); cell.com renders the widget
   lower-left, find it in the screenshot.
4. Wait 6–10 s, re-observe. Success = page navigates to content or the download fires.
   A spinner that runs >30 s = challenge loop: skip this domain now, do others, retry
   later; if it persists, restart Chrome (fresh reputation) and try once more.

## ScienceDirect PDF gate (pdf.sciencedirectassets.com "Security verification")

Appears after clicking View PDF, sometimes on every paper. Click its Turnstile checkbox
(same technique). The PDF then downloads automatically (`1-s2.0-<PII>-main.pdf`). If the
same paper re-challenges later, just repeat the click — it is fast.

## ASH crawl prevention (doi.org redirect path)

Page "Validate User": reCAPTCHA checkbox + "Take me to my Content".
- Preferred: **avoid it entirely** — navigate directly to the full
  `ashpublications.org/blood/article/...` URL instead of `doi.org/...`.
- If unavoidable: click the reCAPTCHA box. An image challenge ("Select all images with
  traffic lights") may pop: `zoom` the 3×3 grid, click every tile containing the object
  (partial/edge occurrences count), click VERIFY. If "Verification challenge expired"
  appears, redo. Challenges can loop for automation — fall back to the direct-URL route
  (search the title to find the canonical article URL).

## Publisher flows that need the article page

- ScienceDirect: article page must show the institutional banner
  ("Brought to you by: <Institution>") and/or "Full text access". Find the
  "View PDF. Opens in a new window." link and AXPress it.
- ASH: link text is like "Open the PDF for <title> in another window".
- NEJM: "View PDF" link in article tools.
- JAMA: "Download PDF" button → sign-in modal. **Stop** — Shibboleth/personal
  credentials must never be entered by the agent. Mark as needs-user-login.
- OUP: if the URL reroutes `fulltext` → `article-abstract`, the institution lacks the
  journal — mark as no-access instead of fighting it.
- Springer: if the article page exposes no PDF/download control at all, there is no
  entitlement — mark as no-access.

## Hygiene

- Archive each downloaded file immediately (move out of ~/Downloads) so the watcher
  never confuses files between papers.
- Non-PDF downloads (HTML bot walls saved as files) → keep as `.badpart` for inspection,
  mark the paper failed, retry after the domain's challenge is passed.
- Many navigation attempts leave tabs behind; every few dozen, close extra tabs via
  AppleScript (`delete tab i of window 1`) to keep Chrome responsive.

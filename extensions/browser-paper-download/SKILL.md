---
name: browser-paper-download
description: Batch-download academic paper PDFs through the user's own Chrome browser so their institutional/subscription access applies, then rename them to the user's preferred pattern (年份_期刊_第一作者_标题.pdf). Use when the user asks to download paper PDFs (e.g., "download the key references", "用我的浏览器下载这些文献"), when papers are paywalled and the user has institutional access, when given a list of PMIDs/DOIs/citations, or when extracting and downloading key/classic references from review documents. Covers PMID→DOI/PMC lookup, publisher direct-PDF URL construction, AppleScript-driven tab navigation, anti-bot (Cloudflare/Turnstile/reCAPTCHA) handling via computer-use, PubMed-metadata renaming, and archiving PDFs into organized folders.
---

# Browser Paper Download

Download paper PDFs through the user's real Chrome (their cookies = institutional access), navigating tabs via AppleScript and watching `~/Downloads`. Direct `curl` fails on PMC, ASH, JAMA, Wiley, Elsevier etc. (403/bot walls), so the browser is mandatory.

**Harness compatibility**: works in any agent that loads Agent Skills (`SKILL.md`) — ZCode, Claude Code, Codex CLI, opencode, Goose, Amp. Install into a harness with `./install.sh <target>` (or `--dest <dir>`) from the repo. The `scripts/` are plain Python 3 and run standalone; only the interactive anti-bot fallback needs a computer-use / GUI-automation tool, and it must drive the user's **real Chrome** — headless or fresh-profile automation has no institutional cookies.

## Workflow

### 1. Build the download queue

From the user's list (PMIDs, DOIs, or citations extracted from documents), resolve IDs with the bundled script:

```bash
python3 scripts/lookup_ids.py --pmids 33108101,25029335 --out queue.json
```

It fills per paper: `pmcid`, `doi`, Elsevier `pii` (via CrossRef alternative-id), Unpaywall OA mirror URLs, and a best-guess direct `url` + `article_url`. Review the queue JSON (fields: `folder`, `name`, `pmid`, `doi`, `pmcid`, `pii`, `url`, `article_url`, `alt_pdfs`).

### 2. One-time Chrome setup

- Toggle **chrome://settings/content/pdfDocuments → 下载 PDF 文件** (Download PDFs). AXPress on the radio often reports "mismatched"; a raw event click on the label text works, then re-observe to confirm `radio 下载 PDF 文件 = 1`.
- Do NOT bother enabling "Allow JavaScript from Apple Events" — tab navigation via `set URL of ...` works without it.
- If the Chrome window is invisible (stuck on another Space after display sleep): quitting and reopening Chrome fixes it; cookies persist. Start `caffeinate` for long batches.

### 3. Batch download

```bash
python3 scripts/download_papers.py queue.json --dest /path/to/PaperFolder
```

The script opens ONE reusable tab, per paper: snapshots `~/Downloads` → sets tab URL → polls for a new non-`.crdownload` file with stable size → checks `%PDF-` magic → moves/renames to `dest/<folder>/<name>.pdf`. Failures are logged (`NO_DOWNLOAD`, `BAD` files kept in `/tmp`) and safe to re-run (existing files skipped).

**Order the queue by route** to amortize anti-bot passes: all PMC first, then group by publisher domain.

### 4. Interactive fallback (computer-use on Chrome)

For papers the direct URL misses, see [references/antibot_playbook.md](references/antibot_playbook.md) for the full click-through procedures. Summary ladder:

1. **Article-page warmup**: navigate to `article_url`, wait ~10 s, then retry the direct `url`.
2. **Article page + PDF link**: observe with `get_app_state`, find the "View PDF"/"Download PDF"/"Open the PDF" link/button, `left_click` the element (AXPress works on links even when it reports "mismatched"). Watch for the resulting tab/verification.
3. **Cloudflare Turnstile** ("正在安全验证 / 请验证您是真人"): the checkbox is usually an AX `checkbox 请验证您是真人 = 0` element; if AXPress fails, `mouse_move` + `left_mouse_down`/`left_mouse_up` at its raster coordinates (commonly ~(243, 402) at default window size). One pass per domain sets the cookie; then batch the rest of that domain.
4. **ScienceDirect PDF gate**: View PDF → `pdf.sciencedirectassets.com/.../cfts/init` "Security verification" page → click Turnstile → PDF auto-downloads. Verification may recur per paper; just repeat.
5. **ASH crawl-prevention** (reCAPTCHA "I'm not a robot" + "Take me to my Content"): triggers on doi.org redirects, NOT on direct article URLs — always navigate to the full `ashpublications.org/blood/article/...` URL. If an image challenge appears, zoom the grid, identify the target objects, click tiles, VERIFY; challenges can expire — redo if needed.
6. **STOP on login walls**: Shibboleth/personal logins (JAMA "Access through your institution" → sign-in form, NEJM sign-in) — never enter credentials. Skip and report to the user.

### 5. Rename to the user's preferred pattern

After downloading, rename PDFs to **`年份_期刊缩写_第一作者姓_标题.pdf`**
(the user's stated preference, e.g. `2020_N Engl J Med_Beck_Somatic Mutations in UBA1 and Severe Adult-Onset Autoinflammatory Disease.pdf`):

```bash
python3 scripts/rename_papers.py queue.json --dest /path/to/PaperFolder [--dry-run]
```

Metadata (year / journal / first-author surname / title) comes from PubMed esummary
by PMID. It sanitizes filesystem-illegal characters (`/` → `-`, strips e-pub tags),
truncates over-long titles at a word boundary, and disambiguates collisions with
" (2)" suffixes. Always `--dry-run` first when unsure. If the user specifies a
different pattern, adapt `build_name()` in the script.

### 6. Verify and report

Check each archived file is a real PDF (`%PDF-` magic, page count). Report per paper: downloaded (with route used), skipped-no-access (e.g., Springer 1973 journal with no institutional entitlement), needs-user-login (JAMA/NEJM Shibboleth), or unavailable.

## Key route rules

- **PMCID exists** → `https://pmc.ncbi.nlm.nih.gov/articles/{pmcid}/pdf/`. Exception: Blood/JAMA records in PMC are author manuscripts with no PDF (NO_DOWNLOAD) — use the publisher instead.
- **Per-publisher direct URL patterns** (Nature `.pdf`, Wiley `pdfdirect`, Springer `content/pdf`, NEJM `pdf?download=true`, ScienceDirect `pdfft`, ASH `article-pdf`, JAMA `articlepdf`): see [references/publisher_patterns.md](references/publisher_patterns.md). Read it before constructing URLs; several publishers need the cookie from a passed challenge first.
- **Unpaywall mirrors** (`alt_pdfs`) often carry direct PDFs (e.g., ASH `article-pdf` links) usable after the domain's challenge is passed.

## Resources

### scripts/
- `lookup_ids.py` — PMID → PMCID/DOI/Elsevier-PII/Unpaywall resolution; emits queue JSON.
- `download_papers.py` — sequential Chrome-tab downloader with Downloads watcher, PDF validation, archiving, logging.
- `rename_papers.py` — post-download rename to `年份_期刊_第一作者_标题.pdf` via PubMed metadata.

### references/
- `publisher_patterns.md` — per-publisher direct-PDF URL patterns and known quirks (tested in practice).
- `antibot_playbook.md` — Cloudflare/Turnstile/reCAPTCHA/ScienceDirect-verification click procedures and failure modes.

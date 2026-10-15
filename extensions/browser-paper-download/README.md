# browser-paper-download

An agent skill that batch-downloads academic paper PDFs **through your own Chrome browser** — so your institutional / subscription access applies — and renames them to `年份_期刊缩写_第一作者姓_标题.pdf` (e.g. `2020_N Engl J Med_Beck_Somatic Mutations in UBA1.pdf`) using PubMed metadata.

Direct `curl`/`wget` downloads fail on PMC, ASH, JAMA, Wiley, Elsevier, etc. (403s and bot walls). This skill drives your real browser instead: Python + AppleScript navigate a single reusable tab, a watcher archives each finished download, and an anti-bot playbook tells the agent how to click through Cloudflare Turnstile / reCAPTCHA gates when they appear (via a computer-use tool). It never enters credentials — login walls are skipped and reported.

## What's inside

```
SKILL.md                        # main workflow (start here)
scripts/lookup_ids.py           # PMID → PMCID / DOI / Elsevier PII / Unpaywall mirrors → queue.json
scripts/download_papers.py      # sequential Chrome-tab downloader with ~/Downloads watcher + PDF validation
scripts/rename_papers.py        # rename PDFs via PubMed esummary metadata
references/publisher_patterns.md  # per-publisher direct-PDF URL patterns & quirks
references/antibot_playbook.md    # Cloudflare/Turnstile/reCAPTCHA/ScienceDirect click procedures
install.sh                        # install into a harness's skills directory (see below)
```

## Requirements

- macOS + Google Chrome (default PDF setting: chrome://settings/content/pdfDocuments → Download PDFs)
- Python 3 (standard library only — no pip installs)
- Any agent harness that loads Agent Skills (`SKILL.md`) — see the table below. For the interactive anti-bot fallback the harness needs a **computer-use / GUI-automation** tool that drives your real Chrome; the scripts themselves run standalone.

## Install

Clone and run the installer for your harness:

```bash
git clone https://github.com/operoncao123/browser-paper-download.git
cd browser-paper-download
./install.sh claude        # or: zcode codex opencode goose amp agents
./install.sh all           # every harness already installed on this machine
./install.sh --dest ~/some/other/skills-dir   # anything else
```

| Harness | Global skill directory | Project directory | Notes |
|---|---|---|---|
| ZCode | `~/.zcode/skills/` | — | |
| Claude Code | `~/.claude/skills/` | `.claude/skills/` | |
| Codex CLI | `~/.codex/skills/` (`$CODEX_HOME/skills/`) | `.codex/skills/` | restart Codex to pick up new skills |
| opencode | `~/.config/opencode/skills/` | `.opencode/skills/` | |
| Goose | `~/.config/goose/skills/` | `.goose/skills/` | also reads the portable `~/.agents/skills/` |
| Amp | `~/.config/amp/skills/` | — | |

`all` only installs into harnesses whose config directory already exists (`--force` creates the rest). Re-running updates in place. The installer copies just the skill payload (`SKILL.md`, `references/`, `scripts/`) and strips `__pycache__`/`.DS_Store`.

Anti-bot clicking needs a computer-use tool against your real Chrome (institutional cookies); a headless or fresh-profile browser has no access.

## Usage

Ask your agent, e.g. *"download these references with my browser"* and give it PMIDs / DOIs / citations, or run the scripts yourself:

```bash
python3 scripts/lookup_ids.py --pmids 33108101,25029335 --out queue.json
python3 scripts/download_papers.py queue.json --dest ~/Papers
python3 scripts/rename_papers.py queue.json --dest ~/Papers --dry-run   # then without --dry-run
```

## Notes & disclaimer

- Downloads use **your own legitimate access** (institutional subscription cookies or open-access mirrors from Unpaywall). No shadow libraries are involved.
- Automating CAPTCHA / anti-bot challenges may violate publisher terms of use; you're responsible for how you use it. Keep batches modest and human-paced.
- `lookup_ids.py` queries NCBI idconv/eutils, CrossRef, and Unpaywall public APIs. For heavy use, swap the Unpaywall placeholder email (`research@example.org`) for your own contact address as their API policy requests.
- Everything runs locally; no paper lists or credentials leave your machine except the public API lookups above.

## License

[MIT](LICENSE)

## 本地 Windows 适配

本机使用 `windows/browser-下载适配-v1.py`，由 Sci-Browser 项目 `scripts/papers-论文下载-v1.ps1` 调用。使用说明见项目 `docs/论文下载工具使用说明.md`。环境安装：`py -3.12 -m venv venv-3.12`，然后 `venv-3.12/Scripts/python.exe -m pip install -r windows/requirements.txt`。浏览器来自 Sci-Browser 现有 runtime，首次登录使用 setup。

#!/usr/bin/env python3
"""Sequentially download paper PDFs through the user's Chrome and archive them.

Strategy: AppleScript drives ONE reusable Chrome tab (user cookies = institutional
access; no JS-from-AppleEvents needed). For each paper: snapshot ~/Downloads, set
tab URL, poll for a new completed download, validate %PDF magic, move to
<dest>/<folder>/<name>.pdf. Non-PDF downloads are kept aside as .badpart.

Usage:
  python3 download_papers.py queue.json --dest /path/to/PaperFolder [--indices 0 1 5]

Queue JSON: list of {folder, name, url, article_url?}  (see lookup_ids.py)
Re-running skips papers whose destination file already exists (>10 KB).
Anti-bot challenges must be handled interactively between/while runs (see
references/antibot_playbook.md); failed entries are simply re-run afterwards.
"""
import argparse, glob, json, os, shutil, subprocess, time

DL = os.path.expanduser("~/Downloads")


def osa(script, timeout=30):
    return subprocess.run(["osascript", "-e", script],
                          capture_output=True, text=True, timeout=timeout)


def snapshot():
    return set(glob.glob(os.path.join(DL, "*")))


def wait_download(before, timeout=70):
    """Poll Downloads for a NEW file whose size is stable 2 consecutive polls."""
    deadline = time.time() + timeout
    last_new, last_size, stable = None, -1, 0
    while time.time() < deadline:
        time.sleep(1.5)
        candidates = [p for p in glob.glob(os.path.join(DL, "*"))
                      if p not in before
                      and not p.endswith((".crdownload", ".tmp", ".download"))]
        if candidates:
            newest = max(candidates, key=os.path.getmtime)
            size = os.path.getsize(newest)
            if newest == last_new and size == last_size and size > 0:
                stable += 1
                if stable >= 2:
                    return newest
            else:
                stable = 0
            last_new, last_size = newest, size
    return last_new if (last_new and os.path.exists(last_new)) else None


def is_pdf(path):
    try:
        with open(path, "rb") as f:
            return f.read(5) == b"%PDF-"
    except OSError:
        return False


def set_tab_url(url):
    """Reuse the tracked tab if still alive, else open a new one and track it."""
    tabref = "/tmp/paper_dl/.tabid"
    info = None
    if os.path.exists(tabref):
        try:
            info = json.load(open(tabref))
        except Exception:
            info = None
    if info:
        r = osa(f'''
        tell application "Google Chrome"
            repeat with w in windows
                if (id of w) is {info["win"]} then
                    repeat with t in tabs of w
                        if (id of t) is {info["tab"]} then
                            set URL of t to "{url}"
                            return "ok"
                        end if
                    end repeat
                end if
            end repeat
            tell front window to set URL of active tab to "{url}"
        end tell''')
        if r.returncode == 0:
            return
    r = osa(f'''
    tell application "Google Chrome"
        activate
        if (count of windows) = 0 then make new window
        tell front window
            set t to make new tab with properties {{URL:"{url}"}}
            return (id of window 1 as string) & "|" & (id of t as string)
        end tell
    end tell''')
    if r.returncode == 0:
        try:
            wid, tid = r.stdout.strip().split("|")
            os.makedirs(os.path.dirname(tabref), exist_ok=True)
            json.dump({"win": int(wid), "tab": int(tid)}, open(tabref, "w"))
        except Exception:
            pass


def process(q, dest_root, bad_dir, timeout):
    folder = q.get("folder") or q.get("disease") or ""
    dest = os.path.join(dest_root, folder, q["name"] + ".pdf")
    if os.path.exists(dest) and os.path.getsize(dest) > 10000:
        return "SKIP(existing)"
    if not q.get("url"):
        return "NO_URL"
    os.makedirs(os.path.join(dest_root, folder), exist_ok=True)
    for attempt in range(2):
        before = snapshot()
        try:
            set_tab_url(q["url"])
        except Exception as e:
            print(f"    osascript error: {e}", flush=True)
        got = wait_download(before, timeout=timeout if attempt == 0 else 50)
        if got:
            break
        time.sleep(3)
    if got and is_pdf(got):
        shutil.move(got, dest)
        return f"OK({os.path.getsize(dest)//1024}KB)"
    if got:
        os.makedirs(bad_dir, exist_ok=True)
        bad = os.path.join(bad_dir, f"{q['name']}.badpart")
        shutil.move(got, bad)
        return f"BAD({os.path.getsize(bad)}B, kept {bad})"
    return "NO_DOWNLOAD"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("queue")
    ap.add_argument("--dest", required=True)
    ap.add_argument("--indices", nargs="*", type=int, default=None)
    ap.add_argument("--timeout", type=int, default=70)
    args = ap.parse_args()

    queue = json.load(open(args.queue, encoding="utf-8"))
    indices = args.indices if args.indices is not None else range(len(queue))
    bad_dir = "/tmp/paper_dl/bad"
    ok = fail = 0
    for i in indices:
        q = queue[i]
        res = process(q, args.dest, bad_dir, args.timeout)
        print(f"[{i}] {q['name']} | {res}", flush=True)
        with open("/tmp/paper_dl/download.log", "a", encoding="utf-8") as log:
            log.write(f"[{i}] {q['name']} | {res}\n")
        ok += res.startswith(("OK", "SKIP"))
        fail += not res.startswith(("OK", "SKIP"))
        time.sleep(2)
    print(f"DONE ok={ok} fail={fail}")


if __name__ == "__main__":
    main()

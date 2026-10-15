#!/usr/bin/env python3
"""Rename downloaded paper PDFs to the user's preferred pattern:

    年份_期刊_第一作者_标题.pdf        e.g. 2020_N Engl J Med_Beck_Somatic mutations in UBA1 and severe adult-onset autoinflammatory disease.pdf

Metadata (year / MEDLINE journal abbreviation / first-author surname / full title)
is fetched from PubMed esummary by PMID, so a queue with `pmid` per paper is
required (see lookup_ids.py).

Usage:
  python3 rename_papers.py queue.json --dest /path/to/PaperFolder [--dry-run]

Re-run is safe: entries whose PDF is missing are skipped, name collisions get
" (2)" suffixes. Non-filesystem-safe characters (/ :) are replaced with "-",
e-pub tags stripped, titles truncated at a word boundary (140 chars).
"""
import argparse, json, os, re, urllib.request


def fetch_meta(pmids):
    url = ("https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esummary.fcgi?db=pubmed&id="
           + ",".join(pmids) + "&retmode=json")
    req = urllib.request.Request(url, headers={"User-Agent": "paper-rename/1.0"})
    with urllib.request.urlopen(req, timeout=60) as r:
        return json.load(r)["result"]


def clean(s):
    s = re.sub(r"<[^>]+>", "", s or "")          # strip e-publishing tags
    s = re.sub(r'[<>:"/\\|?*\x00-\x1f]', "_", s)     # macOS-illegal characters
    return re.sub(r"\s+", " ", s).strip().rstrip(".")


def first_surname(name):
    """'Beck DB' -> 'Beck'; 'Navon Elkan P' -> 'Navon Elkan'; 'de Jesus AA' -> 'de Jesus'."""
    tokens = (name or "").split()
    if not tokens:
        return "Unknown"
    if len(tokens) > 1 and re.fullmatch(r"[A-Za-zÀ-ÿ]{1,4}\.?", tokens[-1]):
        return " ".join(tokens[:-1])
    return tokens[0]


def clip(title, limit=140):
    if len(title) <= limit:
        return title
    return title[:limit].rsplit(" ", 1)[0].rstrip(",;:-")


def build_name(meta):
    year = (meta.get("pubdate") or "YYYY")[:4]
    journal = clean(meta.get("source")) or "Journal"
    first = "Unknown"
    for a in meta.get("authors", []):
        if a.get("authtype") == "CollectiveName":
            continue
        first = first_surname(a.get("name"))
        break
    title = clip(clean(meta.get("title")) or "Untitled")
    return f"{year}_{journal}_{first}_{title}"


def unique_path(path):
    if not os.path.exists(path):
        return path
    base, ext = os.path.splitext(path)
    i = 2
    while os.path.exists(f"{base} ({i}){ext}"):
        i += 1
    return f"{base} ({i}){ext}"


def folder_of(q):
    return q.get("folder") or q.get("disease") or ""


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("queue")
    ap.add_argument("--dest", required=True)
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    queue = json.load(open(args.queue, encoding="utf-8"))
    pmids = [q["pmid"] for q in queue if q.get("pmid")]
    meta = fetch_meta(pmids)

    done = skipped = missing = 0
    for q in queue:
        old = os.path.join(args.dest, folder_of(q), q["name"] + ".pdf")
        if not os.path.exists(old):
            missing += 1
            continue
        m = meta.get(q["pmid"])
        if not m:
            print(f"no metadata for PMID {q['pmid']}, skipped: {q['name']}")
            continue
        new = unique_path(os.path.join(args.dest, folder_of(q),
                                       build_name(m) + ".pdf"))
        if os.path.samefile(old, new) if os.path.exists(new) else old == new:
            skipped += 1
            continue
        if args.dry_run:
            print(f"{os.path.basename(old)}\n  -> {os.path.basename(new)}")
        else:
            os.rename(old, new)
            print(f"renamed: {os.path.basename(new)}")
        done += 1
    print(f"\nrenamed={done} unchanged={skipped} missing_pdf={missing}")


if __name__ == "__main__":
    main()

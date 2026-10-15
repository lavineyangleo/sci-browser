#!/usr/bin/env python3
"""Resolve PMIDs into a download queue: PMCID, DOI, Elsevier PII, Unpaywall mirrors,
and best-guess direct PDF / article URLs.

Usage:
  python3 lookup_ids.py --pmids 33108101,25029335 --out queue.json \
      [--map-file papers.txt]   # optional: "folder|name|pmid" lines for folder/name
Queue JSON fields per paper:
  folder, name, pmid, doi, pmcid, pii, url, article_url, alt_pdfs
"""
import argparse, json, os, time, urllib.parse, urllib.request

UA = {"User-Agent": "paper-fetch/1.0 (research use)"}


def _get(url, timeout=30):
    req = urllib.request.Request(url, headers=UA)
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.load(r)


def idconv(pmids):
    url = ("https://www.ncbi.nlm.nih.gov/pmc/utils/idconv/v1.0/?"
           + urllib.parse.urlencode({"ids": ",".join(pmids), "format": "json"}))
    recs = _get(url).get("records", [])
    return {r.get("pmid", ""): {"pmcid": r.get("pmcid", ""), "doi": r.get("doi", "")}
            for r in recs}


def esummary_dois(pmids):
    """Fill DOIs idconv missed (older journals)."""
    url = ("https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esummary.fcgi?db=pubmed&id="
           + ",".join(pmids) + "&retmode=json")
    data = _get(url)
    out = {}
    for pmid in pmids:
        try:
            doc = data["result"][pmid]
            doi = next((i["value"] for i in doc.get("articleids", [])
                        if i["idtype"] == "doi"), "")
            out[pmid] = {"doi": doi, "journal": doc.get("source", "")}
        except KeyError:
            continue
    return out


def crossref_pii(doi):
    """Elsevier PII from CrossRef alternative-id (strip dashes/brackets)."""
    try:
        msg = _get(f"https://api.crossref.org/works/{urllib.parse.quote(doi)}")["message"]
        alts = msg.get("alternative-id", [])
        pii = alts[0].replace("-", "").replace("(", "").replace(")", "") if alts else ""
        primary = msg.get("resource", {}).get("primary", {}).get("URL", "")
        return pii, primary
    except Exception:
        return "", ""


def unpaywall(doi):
    email = os.environ.get("UNPAYWALL_EMAIL", "")
    if not email:
        return []
    try:
        d = _get(f"https://api.unpaywall.org/v2/{urllib.parse.quote(doi)}?email={urllib.parse.quote(email)}")
        pdfs = [l["url_for_pdf"] for l in d.get("oa_locations", []) if l.get("url_for_pdf")]
        return pdfs
    except Exception:
        return []


def direct_url(doi, pmcid, pii):
    if pmcid:
        return f"https://pmc.ncbi.nlm.nih.gov/articles/{pmcid}/pdf/"
    if doi.startswith("10.1016/") and pii:
        return (f"https://www.sciencedirect.com/science/article/pii/{pii}"
                "/pdfft?isDTMRedir=true&download=true")
    if doi.startswith("10.1038/"):
        return f"https://www.nature.com/articles/{doi.split('/', 1)[1]}.pdf"
    if doi.startswith("10.1056/"):
        return f"https://www.nejm.org/doi/pdf/{doi}?download=true"
    if doi.startswith(("10.1002/", "10.1111/")):
        return f"https://onlinelibrary.wiley.com/doi/pdfdirect/{doi}"
    if doi.startswith("10.1007/"):
        return f"https://link.springer.com/content/pdf/{doi}.pdf"
    return ""  # ASH / JAMA / LWW / OUP: see references/publisher_patterns.md


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--pmids", required=True, help="comma-separated PMIDs")
    ap.add_argument("--map-file", help="optional 'folder|name|pmid' lines")
    ap.add_argument("--out", default="queue.json")
    args = ap.parse_args()

    pmids = [p.strip() for p in args.pmids.split(",") if p.strip()]
    label = {}
    if args.map_file:
        for line in open(args.map_file, encoding="utf-8"):
            parts = [p.strip() for p in line.strip().split("|")]
            if len(parts) == 3:
                label[parts[2]] = (parts[0], parts[1])

    conv = idconv(pmids)
    time.sleep(0.5)
    extra = esummary_dois([p for p in pmids if not conv.get(p, {}).get("doi")])

    queue = []
    for pmid in pmids:
        c = conv.get(pmid, {})
        doi = c.get("doi") or extra.get(pmid, {}).get("doi", "")
        pmcid = c.get("pmcid", "")
        pii, article_url = ("", "")
        if doi.startswith("10.1016/"):
            pii, article_url = crossref_pii(doi)
            time.sleep(0.3)
        alt_pdfs = unpaywall(doi) if doi else []
        folder, name = label.get(pmid, ("", f"PMID_{pmid}"))
        q = {"folder": folder, "name": name, "pmid": pmid, "doi": doi,
             "pmcid": pmcid, "pii": pii, "article_url": article_url,
             "alt_pdfs": alt_pdfs, "url": direct_url(doi, pmcid, pii)}
        # prefer OA mirrors when the publisher is hard-walled
        if not q["url"] and alt_pdfs:
            q["url"] = alt_pdfs[0].replace("http://", "https://")
        queue.append(q)
        print(f"{pmid}: pmcid={pmcid or '-'} doi={doi or '-'} pii={pii or '-'} "
              f"url={'Y' if q['url'] else 'N'} oa_mirrors={len(alt_pdfs)}")

    json.dump(queue, open(args.out, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print(f"\nWrote {len(queue)} papers to {args.out}")


if __name__ == "__main__":
    main()

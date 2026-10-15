# Publisher URL patterns & quirks

All patterns verified in practice. `{doi}` = DOI, `{pmcid}` = PMC ID, `{pii}` = Elsevier PII
(uppercase, dashes/brackets stripped — get it from CrossRef `alternative-id`).

Construct per-paper `url` in this order: PMCID (if it will actually serve a PDF) →
publisher direct URL → Unpaywall mirror. Group the queue by publisher so one
Cloudflare pass covers the whole domain batch.

## Route table

| Publisher | Direct PDF URL | Quirks |
|---|---|---|
| PMC (free) | `https://pmc.ncbi.nlm.nih.gov/articles/{pmcid}/pdf/` | Works via Chrome. **Blood/JAMA records in PMC are author manuscripts with no PDF** → NO_DOWNLOAD, use publisher. Old PMC records occasionally need a second attempt (~40 s) on first hit. |
| Nature / Nat Genet / Nat Immunol … | `https://www.nature.com/articles/{doi_suffix}.pdf` (suffix = DOI minus `10.1038/`) | Most reliable direct download; no CF challenge observed. |
| Wiley | `https://onlinelibrary.wiley.com/doi/pdfdirect/{doi}` | `pdfdirect` downloads; `/doi/pdf/` only opens their reader. Cloudflare challenge once per domain; cookie then covers the batch. |
| Wiley (ACR subdomain) | `https://acrjournals.onlinelibrary.wiley.com/doi/pdfdirect/{doi}` | Separate domain = separate Cloudflare pass. |
| Springer | `https://link.springer.com/content/pdf/{doi}.pdf` | Needs entitlement; old journals (e.g., Pediatric Radiology 1973) may have none — article page then shows no PDF link at all → skip as no-access. |
| NEJM | `https://www.nejm.org/doi/pdf/{doi}?download=true` | Cloudflare challenge once per domain. After pass, direct URL works. `?download=true` matters. |
| ScienceDirect (Elsevier) | Article page → click "View PDF" (do NOT rely on `pdfft` direct nav) | `pdfft` direct navigation hits a "Preparing to download" interstitial that stalls. Correct flow: load `https://www.sciencedirect.com/science/article/pii/{pii}` (institutional banner should show) → AXPress the "View PDF. Opens in a new window." link → `pdf.sciencedirectassets.com` Security-verification Turnstile → click checkbox → PDF downloads (`1-s2.0-{PII}-main.pdf`). Verification can recur per paper. |
| ASH (Blood) | `https://ashpublications.org/blood/article-pdf/{vol}/{issue}/{page}/{fileid}/{file}.pdf` | fileid/file NOT derivable — get from Unpaywall `oa_locations` (older Blood is free) or click the article page's "Open the PDF … in another window" link. Direct article URLs are fine; **doi.org redirects trigger a crawl-prevention reCAPTCHA** — avoid. Cloudflare challenge once per domain. |
| JAMA | `https://jamanetwork.com/journals/{j}/articlepdf/{article_id}` | Cloudflare once; then `articlepdf` STILL redirects to fullarticle and the "Download PDF" button opens a **sign-in modal** (personal or Shibboleth) → stop, needs user login. |
| OUP | Article page → PDF link | Often redirects `fulltext` → `article-abstract` when the institution lacks the journal → no access, skip. |
| LWW / Ovid | via `https://doi.org/{doi}` | Lands on ovid.com abstract; PDF usually pay-per-view → typically no access. |
| cell.com (Cell Press legacy) | `https://www.cell.com/article/{pii}/pdf` | Aggressive Cloudflare loop possible; may never pass. Old Cell articles are free — try the ScienceDirect mirror of the same article (search the title + ScienceDirect; PII like `S0006497120468119`) which usually works with the SD flow. |

## Useful crosswalks

- **Old Blood (ASH) ↔ ScienceDirect**: Blood articles also live on ScienceDirect with a
  `S0006-4971...` PII; when ASH blocks, search `title site:sciencedirect.com` and use the SD flow.
- **Unpaywall** `https://api.unpaywall.org/v2/{doi}?email=...` → `oa_locations[].url_for_pdf`
  gives legal OA mirrors (repository PDFs, publisher OA copies). Prefer https versions.
- **NCBI idconv** does not return DOIs for some older records — fall back to esummary `articleids`.

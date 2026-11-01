# `pdf_extract.py` — PDF text extraction tool (module spec)

File: `tools/pdf_extract.py`. Registered in `config.json` as the custom tool
`pdf-extract`. Tests: `tools/tests/test_pdf_extract.py` (offline; the two seams
`http_get` and `open_page_texts` are monkeypatched, and one test builds a real
one-page PDF with pypdf to cover the read path end to end).

## Purpose

web-fetch (trafilatura) returns nothing for PDFs, and the documents this
machine needs — journal articles, theses, conference PDFs — are PDFs. This tool
reads the PDF text layer (pypdf) and either prints it or greps it with page
markers, so a claim can be traced to a page and quoted verbatim. It accepts a
local path or an http(s) URL: the URL case downloads the file once into a cache
and reuses it, which is what makes the tool usable from the research and
discuss agents (they have no shell to download with).

## Interface (the ECA tool contract)

```
python3 tools/pdf_extract.py "PATH_OR_URL" \
    --pattern "REGEX" --mode "lines|text|raw" \
    --max-matches "INT" --context-chars "INT"
```

`path` is the only required tool parameter; every optional parameter may be
passed as an empty string — and an unsubstituted mustache token left in the
command template by an omitted parameter is treated as unset too, so omitting
optional parameters is safe. Manual-only flags (not passed by ECA):
`--pages "1-5,8"`, `--password "PASSWORD"`, `--cache-dir "DIR"`. Unknown
`--flags` are ignored.

| Parameter | Meaning | Default / bounds |
|---|---|---|
| `path` | absolute path, or http(s) URL of a PDF | required |
| `pattern` | regex, applied per line, case-insensitive | empty = no search |
| `mode` | `lines`, `text`, or `raw` | lines if a pattern is given, else text |
| `max_matches` | matches to report | 60, clamped to 1..500 |
| `context_chars` | context on each side of a match | 240, clamped to 40..2000 |

Page reads are capped at 400 pages and text/raw output at 60000 / 200000
characters; whenever a cap binds, the output says so explicitly.

## Output

stdout is the report; notes and errors go to stderr.

```
# pdf-extract: C:/.../paper.pdf | pages_total=27 scanned=27 mode=lines matched=2
[p10] ... the gradient of color function.
```

* header line: resolved local path, total pages the file reports, pages scanned,
  mode, match count (plus a suffix when the read cap bound the search);
* `mode=lines`: one `[pN] text` line per match; the printed window is the
  matched text extended by `context_chars` on both sides, clipped at the line
  ends, original casing preserved (quote it verbatim — display equations are
  only as faithful as the PDF's own text layer);
* `mode=text`: page text with `[pN]` separators; `mode=raw`: without them;
* exit 0 even when nothing matched (a note suggests trying a broader pattern or
  `mode=text`), exit 1 after a single `ERROR:` line, exit 2 for bad arguments.

## URL handling

A URL is downloaded with a browser-like User-Agent and cached as
`%TEMP%/eca-pdf/ MD5-of-url-path (8 hex) _ sanitised-basename .pdf`. The query
string is ignored for the name and the hash, so re-requesting a paywalled link
with a fresh access token hits the same cache. A cached file whose bytes start
with the PDF magic is reused without a request (a `# note: reused cached
download` line says so). A body that is not a PDF is not cached and produces an
explicit error, because that is how a publisher answers a non-browser client.

## Error contract

| Message | Meaning / next step |
|---|---|
| `ERROR: no such file: ...` | path does not exist |
| `ERROR: not a PDF file (no PDF header)` | wrong file, or a saved HTML page |
| `ERROR: the URL did not return a PDF ...` | publisher blocks non-browser clients, or the link is an abstract page: use the PDF link, or read the HTML with web-fetch |
| `ERROR: PDF is encrypted ...` | needs `--password` (CLI) |
| `ERROR: needs the cryptography package` | AES-encrypted PDF: `python -m pip install cryptography` |
| `ERROR: pypdf is not installed` | `python -m pip install pypdf` |
| `# note: no extractable text ... needs OCR` | scanned/image PDF: text extraction cannot help |

## Dependencies

Python 3 + `pypdf` (already installed in this machine's global Python; not a
dependency of any repository). `cryptography` is needed only for AES-encrypted
PDFs. Nothing but the standard library is imported at module import time — pypdf
and urllib are imported inside the functions that need them, so argument
handling and the pure search/report functions run without them.

## Usage

```
paper found by web-search is a PDF
  → pdf-extract(PDF_URL, "surface tension OR curvature", lines, 20, 300)
    → passages with page numbers → quote verbatim, cite the page
whole short document needed
  → pdf-extract(PDF_URL, "", "", text, 0, 0)
local PDF (downloaded earlier, or in the workspace)
  → pdf-extract(C:/path/to/paper.pdf, "Laplace", lines, 10, 200)
```

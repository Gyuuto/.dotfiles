#!/usr/bin/env python3
"""pdf-extract — read text out of a PDF that web-fetch cannot parse.

web-fetch (trafilatura) returns nothing for PDFs, and the papers this machine
actually needs are PDFs. This tool extracts the text layer of a PDF (pypdf) and
either prints it or greps it, with page markers so a quotation can be traced to
a page. It takes a local path OR an http(s) URL (URLs are downloaded once into
a cache dir — research agents have no shell to download with).

Usage (the ECA custom-tool contract, see pdf_extract.md):
    python3 pdf_extract.py "<path-or-url>" --pattern "<regex>" \
        --mode "<lines|text|raw>" --max-matches "<n>" --context-chars "<n>"

Extra flags for manual use (not passed by ECA): --pages "1-5,8",
--password "<owner/user password>", --cache-dir "<dir>", --list-tools.

Arguments left empty, or left as an unsubstituted "{{template}}" token, mean
"unset / default" — so the required-parameter style used by the other ECA tools
works without a placeholder leaking into the parse.

Specification (the behaviour the tests assert):

1. Defaults. `--mode` omitted means: mode=lines when a pattern is given,
   mode=text when it is not (so "give me the whole text" is just omitting
   both). max_matches default 60 (values <=0 or above 500 are clamped to
   60 / 500). context_chars default 240 (values <40 raise to 40; above 2000
   are lowered to 2000). At most MAX_PAGES (400) pages are read, and the header
   line says how many pages were scanned out of how many.
2. Regex is applied per LINE, case-insensitively, in the file's own order
   (page 1 first, lines in stream order). A line is reported once per match,
   capped by max_matches.
3. Output (stdout). First line is metadata:
   `# pdf-extract: <source> | pages_total=N scanned=N mode=... matched=N`
   (pages_total is the page count the file reports; when the read cap binds the
   line ends with ` (read cap 400 of a M-page file)`), then, for mode=lines,
   one `[pN] <text>` line per match, where the printed window is the matched
   text extended by context_chars on BOTH sides (clipped at the line ends); for
   mode=text/raw the page text itself, `[pN]` separated for mode=text and
   unmarked for mode=raw, capped at 60000 / 200000 chars with a trailing note.
4. Errors and notes go to stderr. A hard error prints one `ERROR: ...` line and
   exits 1: missing file, unsupported file (not a PDF by header), encrypted PDF
   without a usable empty password (hint: --password), missing pypdf (hint: pip
   install pypdf), AES-encrypted PDF without cryptography (hint: pip install
   cryptography), URL that answered with something other than a PDF (typical of
   paywalled publishers blocking non-browser clients). Non-fatal notes, each its
   own `# note: ...` line: "no matches", "no extractable text (scanned image
   PDF: needs OCR)", "stopped after max_matches=N", "stopped at the 400-page
   read cap" (the match cap and the page cap are reported separately, never
   merged). Exit 0 with zero matches is a successful run.
5. URL handling. Downloaded files are cached as
   <cache-dir>/<md5(url-path)[:8]>_<sanitized basename> (the query is dropped
   from both the name and the hash, so re-requesting a paywalled link with a
   new access token reuses the file); a cached file whose bytes start with
   `%PDF` is reused without a request. Seam: http_get().
6. Seams (what the tests replace): http_get (network), open_page_texts (pypdf).
   Everything else is pure.

Exit codes: 0 success (including no matches), 1 hard error, 2 bad arguments.
"""
import hashlib
import os
import re
import sys

DEFAULT_MAX_MATCHES = 60
MAX_MATCHES_CAP = 500
DEFAULT_CONTEXT_CHARS = 240
CONTEXT_MIN = 40
CONTEXT_MAX = 2000
MAX_PAGES = 400
TEXT_CHAR_CAP = 60000
RAW_CHAR_CAP = 200000
MODES = ("lines", "text", "raw")


class PdfToolError(Exception):
    """A hard failure: reported as ERROR: <message>, exit code 1."""


def _is_unset(value):
    """Empty string, None, or an unsubstituted Selmer token means unset."""
    if value is None:
        return True
    v = str(value).strip()
    return v == "" or (v.startswith("{{") and v.endswith("}}"))


def _parse_pages(spec):
    """'1-5,8,10-' -> set of 0-based page indices, or None for 'all'."""
    if _is_unset(spec):
        return None
    wanted = set()
    for part in str(spec).split(","):
        part = part.strip()
        if not part:
            continue
        if "-" in part:
            lo, hi = part.split("-", 1)
            lo = int(lo) if lo.strip() else 1
            hi = int(hi) if hi.strip() else MAX_PAGES
        else:
            lo = hi = int(part)
        if lo < 1:
            lo = 1
        for p in range(lo, hi + 1):
            wanted.add(p - 1)
    return wanted or None


def normalise_args(argv):
    """Parse the CLI defensively; returns the option dict (spec 1 applied).

    Tolerates: leading positional path, empty or placeholder values, unknown
    flags (ignored, they come from a template the author did not fill).
    """
    out = {
        "source": None,
        "pattern": "",
        "mode": None,
        "max_matches": DEFAULT_MAX_MATCHES,
        "context_chars": DEFAULT_CONTEXT_CHARS,
        "pages": None,
        "password": "",
        "cache_dir": None,
    }
    flags = {
        "--pattern": "pattern",
        "--mode": "mode",
        "--max-matches": "max_matches",
        "--context-chars": "context_chars",
        "--pages": "pages",
        "--password": "password",
        "--cache-dir": "cache_dir",
        "--path": "source",
    }
    ignore_value = {"--tool"}
    argv = list(argv)
    i = 0
    while i < len(argv):
        tok = argv[i]
        if tok in ignore_value:
            i += 2
            continue
        if tok in flags:
            value = argv[i + 1] if i + 1 < len(argv) else ""
            i += 2
            key = flags[tok]
            if _is_unset(value):
                continue
            if key in ("max_matches", "context_chars"):
                try:
                    out[key] = int(value)
                except ValueError:
                    raise PdfToolError("%s needs an integer, got %r" % (tok, value))
                continue
            if key == "pages":
                try:
                    out["pages"] = _parse_pages(value)
                except ValueError:
                    raise PdfToolError('--pages needs "1-3,5", got %r' % value)
                continue
            out[key] = value
            continue
        if tok.startswith("--"):
            i += 1
            continue
        if out["source"] is None:
            out["source"] = tok
        i += 1

    if out["source"] is None:
        raise PdfToolError("no PDF given: pass a path or an http(s) URL")

    pat = "" if _is_unset(out["pattern"]) else str(out["pattern"])
    out["pattern"] = pat
    explicit = None if _is_unset(out["mode"]) else str(out["mode"]).strip().lower()
    mode = explicit if explicit is not None else ("lines" if pat else "text")
    if mode not in MODES:
        raise PdfToolError("mode must be one of %s, got %r" % ("/".join(MODES), mode))
    out["mode"] = mode

    mm = out["max_matches"]
    mm = DEFAULT_MAX_MATCHES if mm <= 0 else mm
    out["max_matches"] = min(mm, MAX_MATCHES_CAP)

    cc = out["context_chars"]
    out["context_chars"] = min(max(cc, CONTEXT_MIN), CONTEXT_MAX)
    return out


# ---------------------------------------------------------------------------
# seams: network and pypdf
# ---------------------------------------------------------------------------

def default_cache_dir():
    return os.path.join(os.environ.get("TEMP") or "/tmp", "eca-pdf")


def http_get(url):
    """Seam: return the body of a URL as bytes."""
    import urllib.request

    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 (pdf-extract ECA tool)"})
    with urllib.request.urlopen(req, timeout=90) as resp:
        return resp.read()


def cache_path_for(url, cache_dir):
    """Cache filename for a URL: hash of the URL path (query ignored, so a
    re-fetched paywalled link with a new access token hits the same cache),
    plus a sanitised basename, under cache_dir."""
    base = url.split("?", 1)[0].rstrip("/")
    name = base.split("/")[-1] or "document.pdf"
    name = "".join(c for c in name if c.isalnum() or c in "._-")[:80] or "document.pdf"
    if not name.lower().endswith(".pdf"):
        name += ".pdf"
    return os.path.join(cache_dir, hashlib.md5(base.encode("utf-8")).hexdigest()[:8] + "_" + name)


def resolve_source(source, cache_dir=None):
    """Seam-backed: turn a path or URL into (local_pdf_path, note_or_None)."""
    src = source.strip().strip('"')
    if not re.match(r"(?i)^https?://", src):
        path = os.path.abspath(os.path.expanduser(src))
        if not os.path.isfile(path):
            raise PdfToolError("no such file: %s" % path)
        return path, None

    cache_dir = cache_dir or default_cache_dir()
    try:
        os.makedirs(cache_dir, exist_ok=True)
    except OSError:
        pass
    dest = cache_path_for(src, cache_dir)
    if os.path.isfile(dest) and open(dest, "rb").read(4) == b"%PDF":
        return dest, "reused cached download: %s" % dest
    try:
        body = http_get(src)
    except Exception as exc:  # urllib raises many shapes
        raise PdfToolError("download failed for %s: %s" % (src, exc))
    head = body[:256].lstrip()
    if not head.startswith(b"%PDF"):
        raise PdfToolError(
            "the URL did not return a PDF (starts with %r) — the publisher likely serves HTML "
            "to non-browser clients or the paper is paywalled: %s" % (head[:24].decode("latin-1", "replace"), src)
        )
    with open(dest, "wb") as fh:
        fh.write(body)
    return dest, "downloaded to %s (%d kB)" % (dest, len(body) // 1024)


def open_page_texts(path, password=""):
    """Seam: return the text of every page of the PDF (list of str).

    Maps the failure modes spec 4 names. Reads at most MAX_PAGES pages.
    """
    try:
        from pypdf import PdfReader
        from pypdf.errors import PdfReadError
    except ImportError:
        raise PdfToolError("pypdf is not installed: run 'python -m pip install pypdf'")

    try:
        with open(path, "rb") as fh:
            head = fh.read(1024)
        if not head.lstrip().startswith(b"%PDF"):
            raise PdfToolError("not a PDF file (no %%PDF header): %s" % path)
        reader = PdfReader(path)
        if reader.is_encrypted:
            if not reader.decrypt(password or ""):
                raise PdfToolError(
                    "PDF is encrypted and the empty password was rejected; pass --password (for "
                    "AES-encrypted files 'pip install cryptography' is also required)"
                )
        texts = []
        try:
            total = len(reader.pages)
        except Exception:
            total = MAX_PAGES
        index = 0
        while index < total and index < MAX_PAGES:
            try:
                page = reader.pages[index]
            except Exception:
                if index == 0:
                    raise
                break
            try:
                texts.append(page.extract_text() or "")
            except Exception:
                texts.append("")
            index += 1
        return texts, total
    except PdfToolError:
        raise
    except Exception as exc:
        name = type(exc).__name__
        if "cryptography" in str(exc) or "DependNotFound" in name:
            raise PdfToolError("this PDF needs the 'cryptography' package to decrypt AES: run 'python -m pip install cryptography'")
        if isinstance(exc, PdfReadError):
            raise PdfToolError("pypdf could not read the PDF: %s (%s)" % (exc, path))
        raise PdfToolError("pypdf failed on %s: %s: %s" % (path, name, exc))


# ---------------------------------------------------------------------------
# pure core
# ---------------------------------------------------------------------------

def scan_lines(page_texts, pattern, max_matches, context_chars, pages=None):
    """Return (matches, scanned_pages, total_pages, hit_match_cap, hit_page_cap).

    matches are (page_number_1based, snippet). Pure: no file, no network. The
    two caps are reported separately so the caller can say which one bound the
    search.
    """
    rx = re.compile(pattern, re.IGNORECASE)
    total = len(page_texts)
    matches = []
    scanned = 0
    hit_page_cap = False
    for index, text in enumerate(page_texts):
        if pages is not None and index not in pages:
            continue
        if scanned >= MAX_PAGES:
            hit_page_cap = True
            break
        scanned += 1
        for line in text.splitlines():
            for m in rx.finditer(line):
                start = max(0, m.start() - context_chars)
                end = min(len(line), m.end() + context_chars)
                matches.append((index + 1, line[start:end].strip()))
                if len(matches) >= max_matches:
                    return matches, scanned, total, True, hit_page_cap
    return matches, scanned, total, False, hit_page_cap


def join_text(page_texts, marked, char_cap, pages=None):
    """Concatenate page text; mode=text inserts [pN] markers. Returns (text, truncated)."""
    parts = []
    size = 0
    truncated = False
    for index, text in enumerate(page_texts):
        if pages is not None and index not in pages:
            continue
        piece = ("[p%d] " % (index + 1)) + text if marked else text
        parts.append(piece)
        size += len(piece)
        if size >= char_cap:
            truncated = True
            break
    body = ("\n" if marked else "\n\n").join(parts)
    if len(body) > char_cap:
        body = body[:char_cap]
        truncated = True
    return body, truncated


def run(argv, stdout=None, stderr=None):
    """Execute the tool. Returns the exit code (spec 1-5)."""
    stdout = stdout if stdout is not None else sys.stdout
    stderr = stderr if stderr is not None else sys.stderr
    try:
        args = normalise_args(argv)
        source, note = resolve_source(args["source"], args["cache_dir"])
        page_texts, declared_pages = open_page_texts(source, args["password"])
    except PdfToolError as exc:
        print("ERROR: %s" % exc, file=stderr)
        return 1

    if note:
        print("# note: %s" % note, file=stderr)
    if not any(t.strip() for t in page_texts):
        print("# note: no extractable text in %d page(s) — a scanned/image PDF needs OCR"
              % len(page_texts), file=stderr)

    searchable = len(page_texts)
    pages_note = "" if searchable == declared_pages else " (read cap %d of a %d-page file)" % (MAX_PAGES, declared_pages)

    if args["mode"] == "lines":
        matches, scanned, total, hit_match_cap, hit_page_cap = scan_lines(
            page_texts, args["pattern"], args["max_matches"], args["context_chars"], args["pages"])
        print("# pdf-extract: %s | pages_total=%d scanned=%d mode=lines matched=%d%s"
              % (source, declared_pages, scanned, len(matches), pages_note), file=stdout)
        for page_no, snippet in matches:
            print("[p%d] %s" % (page_no, snippet), file=stdout)
        if not matches:
            print("# note: no matches — try a broader pattern, another spelling, or mode=text",
                  file=stderr)
        if hit_match_cap:
            print("# note: stopped after max_matches=%d matches; more text may follow"
                  % args["max_matches"], file=stderr)
        if hit_page_cap:
            print("# note: stopped at the %d-page read cap" % MAX_PAGES, file=stderr)
        return 0

    marked = args["mode"] == "text"
    cap = TEXT_CHAR_CAP if marked else RAW_CHAR_CAP
    body, truncated = join_text(page_texts, marked, cap, args["pages"])
    print("# pdf-extract: %s | pages_total=%d scanned=%d mode=%s chars=%d%s"
          % (source, declared_pages, searchable, args["mode"], len(body), pages_note), file=stdout)
    print(body, file=stdout)
    if truncated:
        print("# note: output capped at %d characters (use mode=lines with --pattern to read "
              "targeted passages)" % cap, file=stderr)
    return 0


def main(argv=None):
    return run(sys.argv[1:] if argv is None else argv)


if __name__ == "__main__":
    sys.exit(main())

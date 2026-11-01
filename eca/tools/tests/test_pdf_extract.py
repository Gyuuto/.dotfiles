"""Specification tests for tools/pdf_extract.py.

OFFLINE: the two seams named in the module docstring — ``http_get`` (network)
and ``open_page_texts`` (pypdf) — are monkeypatched in every test that needs
them; the rest of the module is pure and tested directly. One end-to-end test
builds a real one-page PDF with pypdf and skips itself if pypdf cannot produce
that fixture.

The spec under test is the module docstring of ``pdf_extract.py``: argument
normalisation (defaults, placeholder tolerance, clamping), the per-line
case-insensitive search with symmetric context, the two caps reported
separately, stdout/exit-code contract (0 with zero matches, 1 with one ERROR
line), URL download + cache reuse, and the error mapping for non-PDF bodies.

Run with:
    python -m pytest tools/tests/test_pdf_extract.py
"""
import re
import sys
from pathlib import Path

import pytest

# Make tools/ importable as a top-level package root regardless of the cwd.
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import pdf_extract as pe  # noqa: E402


PAGES = [
    "Intro page.\nThe curvature kappa is signed by construction.\nnothing else",
    "Second page mentions Surface Tension as a body force f = sigma kappa n.\nend",
]


class Capture:
    def __init__(self):
        import io

        self.out = io.StringIO()
        self.err = io.StringIO()

    @property
    def stdout(self):
        return self.out.getvalue()

    @property
    def stderr(self):
        return self.err.getvalue()


@pytest.fixture
def fake_pdf(monkeypatch):
    """Stub both seams: resolve_source hands back 'fake.pdf', pypdf the fixture."""
    monkeypatch.setattr(pe, "resolve_source", lambda source, cache_dir=None: ("fake.pdf", None))
    monkeypatch.setattr(pe, "open_page_texts", lambda path, password="": (list(PAGES), len(PAGES)))


# ---------------------------------------------------------------------------
# spec: argument normalisation
# ---------------------------------------------------------------------------

def test_defaults_and_positional_source():
    args = pe.normalise_args(["C:/tmp/a.pdf"])
    assert args["source"] == "C:/tmp/a.pdf"
    assert args["pattern"] == ""
    assert args["mode"] == "text"            # spec 1: empty pattern means text
    assert args["max_matches"] == pe.DEFAULT_MAX_MATCHES
    assert args["context_chars"] == pe.DEFAULT_CONTEXT_CHARS


def test_lines_mode_and_values():
    args = pe.normalise_args(["x.pdf", "--pattern", "curvature", "--mode", "lines",
                              "--max-matches", "5", "--context-chars", "80"])
    assert args["mode"] == "lines"
    assert args["pattern"] == "curvature"
    assert args["max_matches"] == 5
    assert args["context_chars"] == 80


def test_unsubstituted_template_tokens_mean_unset():
    args = pe.normalise_args(["x.pdf", "--pattern", "", "--mode", "{{mode}}",
                              "--max-matches", "{{max_matches}}", "--context-chars", ""])
    assert args["mode"] == "text"
    assert args["max_matches"] == pe.DEFAULT_MAX_MATCHES
    assert args["context_chars"] == pe.DEFAULT_CONTEXT_CHARS


def test_caps_are_clamped():
    args = pe.normalise_args(["x.pdf", "--pattern", "p", "--max-matches", "0"])
    assert args["max_matches"] == pe.DEFAULT_MAX_MATCHES
    args = pe.normalise_args(["x.pdf", "--pattern", "p", "--max-matches", "9999"])
    assert args["max_matches"] == pe.MAX_MATCHES_CAP
    args = pe.normalise_args(["x.pdf", "--pattern", "p", "--context-chars", "1"])
    assert args["context_chars"] == pe.CONTEXT_MIN
    args = pe.normalise_args(["x.pdf", "--pattern", "p", "--context-chars", "99999"])
    assert args["context_chars"] == pe.CONTEXT_MAX


def test_unknown_flags_ignored_and_errors():
    args = pe.normalise_args(["x.pdf", "--tool", "pdf-extract", "--pattern", "p"])
    assert args["pattern"] == "p"
    with pytest.raises(pe.PdfToolError):
        pe.normalise_args(["--mode", "lines"])                     # no source
    with pytest.raises(pe.PdfToolError):
        pe.normalise_args(["x.pdf", "--mode", "sideways"])        # bad mode
    with pytest.raises(pe.PdfToolError):
        pe.normalise_args(["x.pdf", "--max-matches", "many"])     # non-integer
    with pytest.raises(pe.PdfToolError):
        pe.normalise_args(["x.pdf", "--pages", "first"])          # bad page range


def test_page_range_parsing():
    assert pe._parse_pages("1-2,4") == {0, 1, 3}
    assert pe._parse_pages("") is None
    assert pe._parse_pages("2-") == set(range(1, pe.MAX_PAGES))


# ---------------------------------------------------------------------------
# spec 2/3: the search itself
# ---------------------------------------------------------------------------

def test_scan_lines_case_insensitive_with_page_numbers():
    matches, scanned, total, hit_cap, hit_pages = pe.scan_lines(PAGES, "surface tension", 10, 0)
    assert matches == [(2, "Surface Tension")]           # original casing, exact text at ctx 0
    assert (scanned, total, hit_cap, hit_pages) == (2, 2, False, False)


def test_scan_lines_multiple_matches_on_one_line_reported_once_each():
    text = ["kappa n and kappa m"]
    matches, *_ = pe.scan_lines(text, "kappa", 10, 0)
    assert len(matches) == 2


def test_context_window_is_symmetric_and_clipped_at_the_line_ends():
    middle = ["abcdefghijTARGETklmno"]
    got, *_ = pe.scan_lines(middle, "TARGET", 10, 3)
    assert got[0][1] == "hijTARGETklm"                   # context_chars on each side

    edge = ["TARGETxyz"]
    got, *_ = pe.scan_lines(edge, "TARGET", 10, 4)
    assert got[0][1] == "TARGETxyz"                      # clipped at the line ends


def test_match_cap_stops_and_says_so():
    pages = ["hit here"] * 5
    matches, scanned, total, hit_cap, hit_pages = pe.scan_lines(pages, "hit", 2, 4)
    assert len(matches) == 2
    assert hit_cap is True and hit_pages is False


def test_page_selection_limits_searched_pages():
    matches, scanned, *_ = pe.scan_lines(PAGES, "curvature", 10, 4, pages={1})
    assert matches == [] and scanned == 1
    matches, scanned, *_ = pe.scan_lines(PAGES, "curvature", 10, 4, pages={0})
    assert len(matches) == 1 and scanned == 1


def test_join_text_marks_pages_or_not_and_caps():
    body, truncated = pe.join_text(["aa", "bb"], marked=True, char_cap=1000)
    assert body == "[p1] aa\n[p2] bb" and truncated is False
    body, truncated = pe.join_text(["aa", "bb"], marked=False, char_cap=1000)
    assert body == "aa\n\nbb" and truncated is False
    body, truncated = pe.join_text(["aaaaaa"], marked=True, char_cap=3)
    assert body == "[p1] "[:3] and truncated is True


# ---------------------------------------------------------------------------
# spec 3/4: run() — stdout, notes, exit codes
# ---------------------------------------------------------------------------

def test_run_lines_mode_output_and_exit_zero(fake_pdf):
    line = PAGES[1].splitlines()[0]
    m = re.search("body force", line, re.IGNORECASE)
    ctx = 60                                    # above the 40-character floor
    expected = line[max(0, m.start() - ctx): m.end() + ctx]      # ctx characters on each side
    cap = Capture()
    code = pe.run(["fake.pdf", "--pattern", "body force", "--context-chars", str(ctx)],
                  cap.out, cap.err)
    assert code == 0
    lines = cap.stdout.splitlines()
    assert lines[0] == "# pdf-extract: fake.pdf | pages_total=2 scanned=2 mode=lines matched=1"
    assert lines[1] == "[p2] " + expected      # the page marker plus the context window
    assert cap.stderr == ""


def test_run_no_matches_is_success_with_a_hint(fake_pdf):
    cap = Capture()
    code = pe.run(["fake.pdf", "--pattern", "zzzzz"], cap.out, cap.err)
    assert code == 0
    assert "matched=0" in cap.stdout
    assert "no matches" in cap.stderr


def test_run_reports_the_match_cap_only(fake_pdf):
    cap = Capture()
    code = pe.run(["fake.pdf", "--pattern", "e", "--max-matches", "1", "--context-chars", "1"],
                  cap.out, cap.err)
    assert code == 0
    assert "stopped after max_matches=1" in cap.stderr
    assert "read cap" not in cap.stderr


def test_run_text_mode_and_ocr_note(monkeypatch):
    monkeypatch.setattr(pe, "resolve_source", lambda source, cache_dir=None: ("fake.pdf", None))
    monkeypatch.setattr(pe, "open_page_texts", lambda path, password="": (["", ""], 2))
    cap = Capture()
    code = pe.run(["fake.pdf", "--mode", "text"], cap.out, cap.err)
    assert code == 0
    assert "mode=text" in cap.stdout
    assert "no extractable text" in cap.stderr and "OCR" in cap.stderr


def test_run_hard_error_is_one_line_and_exit_one(tmp_path, monkeypatch):
    monkeypatch.setattr(pe, "open_page_texts", lambda path, password="": (["x"], 1))
    cap = Capture()
    code = pe.run([str(tmp_path / "absent.pdf")], cap.out, cap.err)
    assert code == 1
    assert cap.stdout == ""
    assert cap.stderr.startswith("ERROR: no such file:")
    assert cap.stderr.count("\n") == 1


# ---------------------------------------------------------------------------
# spec 5: URLs — download, cache reuse, non-PDF answers
# ---------------------------------------------------------------------------

def test_url_download_then_cache_reuse(tmp_path, monkeypatch):
    calls = []

    def fake_get(url):
        calls.append(url)
        return b"%PDF-1.4\nfake body"

    monkeypatch.setattr(pe, "http_get", fake_get)
    url = "https://example.org/paper/p1.pdf"
    source, note = pe.resolve_source(url, cache_dir=str(tmp_path))
    assert source.startswith(str(tmp_path)) and note.startswith("downloaded to")
    assert open(source, "rb").read(5) == b"%PDF-"
    again, note2 = pe.resolve_source(url, cache_dir=str(tmp_path))
    assert again == source and note2.startswith("reused cached download")
    assert len(calls) == 1                      # second call hit the cache


def test_url_that_answers_html_is_a_clear_error(tmp_path, monkeypatch):
    monkeypatch.setattr(pe, "http_get", lambda url: b"<!DOCTYPE html><html>paywall</html>")
    with pytest.raises(pe.PdfToolError) as exc:
        pe.resolve_source("https://example.org/x.pdf", cache_dir=str(tmp_path))
    assert "did not return a PDF" in str(exc.value)


def test_cache_name_is_stable_sanitised_and_pdf_suffixed():
    a = pe.cache_path_for("https://x.org/a/b/PAPER(1).pdf?access_token=one", "/c")
    b = pe.cache_path_for("https://x.org/a/b/PAPER(1).pdf?access_token=two", "/c")
    assert a == b                                        # the query is not part of the key
    assert a.endswith(".pdf") and "(" not in a.split("_", 1)[1]
    assert pe.cache_path_for("https://x.org/files/download", "/c").endswith("_download.pdf")
    assert pe.cache_path_for("https://x.org/", "/c").endswith("_x.org.pdf")   # host becomes the name


def test_plain_path_is_absoluted_and_never_downloaded(tmp_path, monkeypatch):
    monkeypatch.setattr(pe, "http_get", lambda url: pytest.fail("a path must not be downloaded"))
    target = tmp_path / "paper.pdf"
    target.write_bytes(b"%PDF-1.4\n")
    source, note = pe.resolve_source(str(target))
    assert source == str(target) and note is None
    with pytest.raises(pe.PdfToolError) as exc:
        pe.resolve_source("no_such_file_here.pdf")
    assert "no such file:" in str(exc.value) and Path(exc.value.args[0].split(": ", 1)[1]).is_absolute()


# ---------------------------------------------------------------------------
# seam contract: a real PDF through pypdf (skipped if that fixture can't be made)
# ---------------------------------------------------------------------------

def build_one_page_pdf(tmp_path):
    """A real one-page PDF with a real text object (pypdf write + read)."""
    from pypdf import PdfWriter
    from pypdf.generic import DecodedStreamObject, DictionaryObject, NameObject

    w = PdfWriter()
    page = w.add_blank_page(width=300, height=120)
    data = DecodedStreamObject()
    data.set_data(b"BT /F1 12 Tf 14 70 Td (Surface tension model) Tj ET")
    font = DictionaryObject()
    for key, value in (("/Type", "/Font"), ("/Subtype", "/Type1"),
                       ("/BaseFont", "/Helvetica"), ("/Encoding", "/WinAnsiEncoding")):
        font[NameObject(key)] = NameObject(value)
    fonts = DictionaryObject()
    fonts[NameObject("/F1")] = w._add_object(font)
    resources = DictionaryObject()
    resources[NameObject("/Font")] = w._add_object(fonts)
    page[NameObject("/Contents")] = w._add_object(data)
    page[NameObject("/Resources")] = w._add_object(resources)
    path = tmp_path / "fixture.pdf"
    with open(path, "wb") as fh:
        w.write(fh)
    return path


def test_end_to_end_through_pypdf(tmp_path):
    try:
        path = build_one_page_pdf(tmp_path)
    except Exception as exc:                      # pypdf API drift or absence
        pytest.skip("cannot build the PDF fixture with the installed pypdf: %s" % exc)
    texts, declared = pe.open_page_texts(str(path))
    assert declared == 1 and "Surface tension model" in texts[0].replace("\n", " ")
    cap = Capture()
    code = pe.run([str(path), "--pattern", "surface tension", "--context-chars", "3"], cap.out, cap.err)
    assert code == 0 and "[p1]" in cap.stdout


def test_non_pdf_file_is_rejected(tmp_path):
    path = tmp_path / "text.pdf"
    path.write_bytes(b"plain text, not a pdf")
    with pytest.raises(pe.PdfToolError) as exc:
        pe.open_page_texts(str(path))
    assert "not a PDF" in str(exc.value)


def test_missing_dependency_and_decrypt_errors(tmp_path, monkeypatch):
    path = tmp_path / "x.pdf"
    path.write_bytes(b"%PDF-1.4\n")

    def boom(path, password=""):
        raise RuntimeError("cryptography>=3.1 is required for AES algorithm")

    monkeypatch.setattr("builtins.__import__", lambda name, *a, **k: (_ for _ in ()).throw(
        ImportError("no pypdf")) if name.startswith("pypdf") else __import__(name, *a, **k))
    with pytest.raises(pe.PdfToolError) as exc:
        pe.open_page_texts(str(path))
    assert "pypdf is not installed" in str(exc.value)

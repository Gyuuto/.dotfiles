"""Specification tests for tools/danbooru_tags.py.

All tests run OFFLINE: the single HTTP seam ``http_get_json`` is monkeypatched,
so no network access is needed. The spec under test is the module docstring
of ``danbooru_tags.py`` (usage, modes, output sections, verdict thresholds).

Run with:
    python -m pytest tools/tests
"""
import io
import sys
import urllib.parse
import urllib.error
from collections import Counter
from pathlib import Path

import pytest

# Make tools/ importable as a top-level package root regardless of the cwd.
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import danbooru_tags as dt  # noqa: E402


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def make_post(general="", character="", copyright_="", meta="", artist=""):
    """Build a minimal Danbooru post dict from per-category tag strings."""
    return {
        "tag_string_general": general,
        "tag_string_character": character,
        "tag_string_copyright": copyright_,
        "tag_string_meta": meta,
        "tag_string_artist": artist,
    }


def check_url(name):
    """The exact URL check_name() must query for `name`."""
    return "https://danbooru.donmai.us/posts.json?tags=%s&limit=3" % urllib.parse.quote(name, safe="")


def fake_http(analysis_posts, check_responses):
    """Build a fake http_get_json.

    Dispatches on the URL: analysis fetches embed `order:score` in the tags
    value; check probes are bare `tags=<name>&limit=3`.
    """
    def fake(url):
        if "order" in url:
            return analysis_posts
        m = urllib.parse.urlparse(url)
        qs = dict(pair.split("=", 1) for pair in m.query.split("&"))
        name = urllib.parse.unquote(qs["tags"])
        return list(check_responses.get(name, []))
    return fake


def make_http_error(url, code=429, body=b'{"error": "rate limited"}'):
    return urllib.error.HTTPError(url, code, "Too Many Requests", {}, io.BytesIO(body))


ANALYSIS_POSTS = [
    make_post(general="1girl solo blush", character="ganyu", artist="wlop",
              copyright_="genshin_impact", meta="highres"),
    make_post(general="1girl solo", character="ganyu", copyright_="genshin_impact"),
    make_post(general="1girl solo", character="paimon"),
]


# ---------------------------------------------------------------------------
# norm()
# ---------------------------------------------------------------------------

def test_norm_replaces_spaces_with_underscores():
    assert dt.norm("black hair") == "black_hair"


def test_norm_strips_whitespace():
    assert dt.norm("  black hair ") == "black_hair"


def test_norm_empty_string():
    assert dt.norm("") == ""


def test_norm_preserves_special_characters():
    # Tag-intrinsic symbols (underscores, hyphens, parentheses, !) stay as-is.
    assert dt.norm("princess connect!") == "princess_connect!"
    assert dt.norm("fur-trimmed") == "fur-trimmed"


# ---------------------------------------------------------------------------
# verdict() -- documented thresholds
# ---------------------------------------------------------------------------

def test_verdict_absent_zero_count():
    code, _ = dt.verdict(0, 10)
    assert code == "absent"


def test_verdict_absent_zero_total():
    code, _ = dt.verdict(5, 0)
    assert code == "absent"


def test_verdict_adopt_at_30_percent():
    code, msg = dt.verdict(3, 10)
    assert code == "adopt"
    assert "3/10" in msg


def test_verdict_adopt_above_30_percent():
    code, _ = dt.verdict(9, 10)
    assert code == "adopt"


def test_verdict_moderate_between_5_and_30():
    code, msg = dt.verdict(2, 10)
    assert code == "moderate"
    assert "2/10" in msg


def test_verdict_moderate_at_5_percent():
    code, _ = dt.verdict(5, 100)
    assert code == "moderate"


def test_verdict_rare_below_5_percent():
    code, msg = dt.verdict(4, 100)
    assert code == "rare"
    assert "4/100" in msg


# ---------------------------------------------------------------------------
# describe_population()
# ---------------------------------------------------------------------------

def test_describe_population_complete_census():
    s = dt.describe_population(7, 20)
    assert "complete census" in s and "7" in s


def test_describe_population_top200():
    s = dt.describe_population(200, 200)
    assert "top-200 by rating" in s


def test_describe_population_sample():
    s = dt.describe_population(100, 100)
    assert "sample of the top-100" in s


# ---------------------------------------------------------------------------
# render_table()
# ---------------------------------------------------------------------------

def test_render_table_empty_counter():
    assert dt.render_table(Counter(), 10, 5) == []


def test_render_table_rows_and_truncation():
    c = Counter({"a": 9, "b": 8, "c": 7})
    rows = dt.render_table(c, 10, 2)
    assert len(rows) == 2
    assert rows[0].startswith("  1. a")
    assert "9/10" in rows[0]
    assert "90%" in rows[0]


# ---------------------------------------------------------------------------
# count_tags()
# ---------------------------------------------------------------------------

def test_count_tags_aggregates_per_category():
    posts = [
        make_post(general="1girl solo blush", character="ganyu"),
        make_post(general="1girl solo", character="ganyu", artist="wlop"),
    ]
    counters, artist = dt.count_tags(posts)
    assert counters["general"]["1girl"] == 2
    assert counters["general"]["blush"] == 1
    assert counters["character"]["ganyu"] == 2
    assert artist["wlop"] == 1


def test_count_tags_excludes_noise():
    posts = [make_post(general="1girl highres absurdres")]
    counters, _ = dt.count_tags(posts)
    assert "highres" not in counters["general"]
    assert "absurdres" not in counters["general"]
    assert counters["general"]["1girl"] == 1


# ---------------------------------------------------------------------------
# post_tag_set() / alias_candidates()
# ---------------------------------------------------------------------------

def test_post_tag_set_unions_all_categories():
    p = make_post(general="a b", character="c", meta="a")
    assert dt.post_tag_set(p) == {"a", "b", "c"}


def test_post_tag_set_missing_fields():
    assert dt.post_tag_set({}) == set()


def test_alias_candidates_intersection_minus_noise_and_name():
    p1 = make_post(general="1girl solo azuki_(moromoro)")
    p2 = make_post(general="1girl solo azuki_(moromoro)")
    cands = dt.alias_candidates([p1, p2], "azuki")
    assert "azuki_(moromoro)" in cands
    assert "azuki" not in cands


def test_alias_candidates_empty_input():
    assert dt.alias_candidates([], "x") == []


def test_alias_candidates_respects_cap():
    tags = " ".join("t%d" % i for i in range(30))
    p = make_post(general=tags)
    cands = dt.alias_candidates([p], "x", cap=5)
    assert len(cands) == 5


# ---------------------------------------------------------------------------
# fetch() / check_name() -- URL building and error handling
# ---------------------------------------------------------------------------

def test_fetch_builds_rating_order_url(monkeypatch):
    captured = {}

    def fake(url):
        captured["url"] = url
        return [make_post(general="x")]

    monkeypatch.setattr(dt, "http_get_json", fake)
    posts, ntag, url = dt.fetch("black hair", 50)
    assert ntag == "black_hair"
    assert posts == [make_post(general="x")]
    assert "tags=black_hair+rating%3As+order%3Ascore" in url
    assert "limit=50" in url


def test_fetch_empty_tag_raises():
    with pytest.raises(ValueError):
        dt.fetch("   ", 10)


def test_check_name_builds_bare_tags_url(monkeypatch):
    captured = {}

    def fake(url):
        captured["url"] = url
        return []

    monkeypatch.setattr(dt, "http_get_json", fake)
    posts, n, url = dt.check_name("legs apart")
    assert n == "legs_apart"
    assert posts == []
    assert url == check_url("legs_apart")


def test_check_name_empty_name_raises():
    with pytest.raises(ValueError):
        dt.check_name("  ")


# ---------------------------------------------------------------------------
# render_check_section() -- the three verdict paths + error path
# ---------------------------------------------------------------------------

def test_render_check_section_canonical(monkeypatch):
    monkeypatch.setattr(dt, "http_get_json", lambda url: [make_post(general="motion_blur x")])
    out = dt.render_check_section(["motion_blur"])
    assert out[0] == "## Tag existence check"
    assert any("[EXISTS] canonical tag" in line and "`motion_blur`" in line for line in out)


def test_render_check_section_alias_lists_candidates(monkeypatch):
    monkeypatch.setattr(dt, "http_get_json",
                        lambda url: [make_post(general="1girl solo azuki_(moromoro)")])
    out = dt.render_check_section(["azuki"])
    assert any("[ALIAS]" in line for line in out)
    assert any("`azuki_(moromoro)`" in line for line in out)


def test_render_check_section_not_found(monkeypatch):
    monkeypatch.setattr(dt, "http_get_json", lambda url: [])
    out = dt.render_check_section(["nonexistent_zzz"])
    assert any("[NOT FOUND]" in line and "nonexistent_zzz" in line for line in out)


def test_render_check_section_error_does_not_abort(monkeypatch):
    def fake(url):
        raise OSError("boom")

    monkeypatch.setattr(dt, "http_get_json", fake)
    out = dt.render_check_section(["a", "b"])
    assert sum("[ERROR]" in line for line in out) == 2
    # The trailing note is still present.
    assert any(line.startswith("Note: EXISTS/ALIAS") for line in out)


def test_render_check_section_normalizes_space_form(monkeypatch):
    captured = {}

    def fake(url):
        captured["url"] = url
        return [make_post(general="legs_apart")]

    monkeypatch.setattr(dt, "http_get_json", fake)
    out = dt.render_check_section(["legs apart"])
    assert captured["url"] == check_url("legs_apart")
    assert any("`legs_apart`" in line for line in out)


# ---------------------------------------------------------------------------
# main() -- mode dispatch, validation, error paths (offline)
# ---------------------------------------------------------------------------

def test_main_check_only_mode(monkeypatch, capsys):
    monkeypatch.setattr(sys, "argv",
                        ["danbooru_tags.py", "", "--limit", "1",
                         "--verify", "", "--check", "motion_blur,nonexistent_zzz"])
    monkeypatch.setattr(dt, "http_get_json",
                        fake_http([], {"motion_blur": [make_post(general="motion_blur")],
                                        "nonexistent_zzz": []}))
    dt.main()
    out = capsys.readouterr().out
    assert "# Danbooru Tag Check (existence verification)" in out
    assert "Names checked: 2" in out
    assert "## Tag existence check" in out
    assert "[EXISTS]" in out
    assert "[NOT FOUND]" in out
    # No analysis sections in check-only mode.
    assert "## General / descriptive tags" not in out
    assert "- Population:" not in out


def test_main_analysis_only_mode_preserves_format(monkeypatch, capsys):
    monkeypatch.setattr(sys, "argv",
                        ["danbooru_tags.py", "ganyu", "--limit", "10",
                         "--verify", "genshin_impact", "--check", ""])
    monkeypatch.setattr(dt, "http_get_json", fake_http(ANALYSIS_POSTS, {}))
    dt.main()
    out = capsys.readouterr().out
    # Established analysis format is intact.
    assert "# Danbooru Tag Analysis: ganyu\n" in out
    # 3 posts returned < limit 10 -> complete census description.
    assert "- Population: complete census (all 3 matching SFW posts returned" in out
    assert "## General / descriptive tags" in out
    assert "## Character tags" in out
    assert "## Copyright / work tags" in out
    assert "## Candidate tag verification" in out
    # 1/3 posts carry the copyright tag -> 33% -> ADOPT.
    assert "`genshin_impact`  [ADOPT]" in out
    # No check section when --check is empty.
    assert "## Tag existence check" not in out


def test_main_analysis_plus_check_appends_section(monkeypatch, capsys):
    monkeypatch.setattr(sys, "argv",
                        ["danbooru_tags.py", "ganyu", "--limit", "10",
                         "--verify", "", "--check", "penetration"])
    monkeypatch.setattr(dt, "http_get_json",
                        fake_http(ANALYSIS_POSTS, {"penetration": []}))
    dt.main()
    out = capsys.readouterr().out
    assert "## General / descriptive tags" in out
    assert "## Tag existence check" in out
    assert "[NOT FOUND]" in out
    # Check section is appended AFTER the analysis report.
    assert out.index("## General / descriptive tags") < out.index("## Tag existence check")


def test_main_both_empty_errors(monkeypatch, capsys):
    monkeypatch.setattr(sys, "argv",
                        ["danbooru_tags.py", "", "--limit", "1",
                         "--verify", "", "--check", ""])
    with pytest.raises(SystemExit) as exc:
        dt.main()
    assert exc.value.code == 1
    assert "either the tag or --check must be non-empty" in capsys.readouterr().err


def test_main_bad_limit_with_tag_errors(monkeypatch, capsys):
    monkeypatch.setattr(sys, "argv",
                        ["danbooru_tags.py", "ganyu", "--limit", "0",
                         "--verify", "", "--check", ""])
    with pytest.raises(SystemExit) as exc:
        dt.main()
    assert exc.value.code == 1
    assert "--limit must be between 1 and 200" in capsys.readouterr().err


def test_main_bad_limit_in_check_only_mode_is_ignored(monkeypatch, capsys):
    monkeypatch.setattr(sys, "argv",
                        ["danbooru_tags.py", "", "--limit", "0",
                         "--verify", "", "--check", "motion_blur"])
    monkeypatch.setattr(dt, "http_get_json",
                        fake_http([], {"motion_blur": [make_post(general="motion_blur")]}))
    dt.main()
    out = capsys.readouterr().out
    assert "[EXISTS]" in out


def test_main_tag_not_found_report(monkeypatch, capsys):
    monkeypatch.setattr(sys, "argv",
                        ["danbooru_tags.py", "no_such_tag", "--limit", "10",
                         "--verify", "", "--check", ""])
    monkeypatch.setattr(dt, "http_get_json", fake_http([], {}))
    dt.main()
    out = capsys.readouterr().out
    assert "## WARNING: TAG NOT FOUND" in out
    assert "SFW posts matched: **0**" in out


def test_main_http_error_exits_1(monkeypatch, capsys):
    monkeypatch.setattr(sys, "argv",
                        ["danbooru_tags.py", "ganyu", "--limit", "10",
                         "--verify", "", "--check", ""])
    def boom(url):
        raise make_http_error(url)

    monkeypatch.setattr(dt, "http_get_json", boom)
    with pytest.raises(SystemExit) as exc:
        dt.main()
    assert exc.value.code == 1
    err = capsys.readouterr().err
    assert "HTTP Error 429" in err


def test_main_unexpected_response_exits_1(monkeypatch, capsys):
    monkeypatch.setattr(sys, "argv",
                        ["danbooru_tags.py", "ganyu", "--limit", "10",
                         "--verify", "", "--check", ""])
    monkeypatch.setattr(dt, "http_get_json", lambda url: {"unexpected": True})
    with pytest.raises(SystemExit) as exc:
        dt.main()
    assert exc.value.code == 1
    assert "unexpected API response" in capsys.readouterr().err


def test_main_verify_parsing_handles_semicolons(monkeypatch, capsys):
    monkeypatch.setattr(sys, "argv",
                        ["danbooru_tags.py", "ganyu", "--limit", "10",
                         "--verify", "a;b, c", "--check", ""])
    monkeypatch.setattr(dt, "http_get_json", fake_http(ANALYSIS_POSTS, {}))
    dt.main()
    out = capsys.readouterr().out
    assert "`a`  [ABSENT]" in out
    assert "`b`  [ABSENT]" in out
    assert "`c`  [ABSENT]" in out

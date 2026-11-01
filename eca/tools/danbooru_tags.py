#!/usr/bin/env python3
"""
danbooru_tags.py — Danbooru tag-usage analyzer for building accurate prompts.

Fetches the SFW posts on Danbooru that carry a given tag and reports how
commonly the co-occurring tags are used. This gives you *model-supported*
ground truth for a character's / work's / concept's tag vocabulary, so the
prompt's tag line is built from tags the model has actually seen (instead of
guessed tags), and so you know which of your own candidate tags to express in
natural language instead.

Why a tool and not a manual API call?
    Danbooru's single-tag "show" endpoint (tags/<name>.json) is unreliable: it
    returns 404 RecordNotFound even for tags that are demonstrably in use.
    The POSTS search endpoint (posts.json?tags=...) is the reliable way to
    confirm a tag exists and to inspect what it is actually used with. This
    script wraps exactly that, handles URL encoding, and turns the raw JSON
    into a readable, decision-ready report.

Only the Python standard library is used (urllib, json, argparse, collections),
so there are no third-party dependencies to install.

Usage:
    python3 danbooru_tags.py <tag> --limit <N> --verify "<t1>,<t2>,..." [--check "<n1>,<n2>,..."]

Modes:
    Analysis mode  (tag non-empty): sample the most-rated SFW posts carrying the
              tag and report the co-occurring tag vocabulary (frequency tables +
              optional --verify candidate verdicts).
    Check-only mode (tag empty, --check non-empty): verify, for each exact tag
              name, whether it resolves to real posts. No sampling is performed;
              --limit/--verify are ignored.
    Both can be combined (analysis + a "## Tag existence check" section).

Arguments:
    tag      (positional)            The Danbooru tag to analyze: a character
              tag (e.g. ishizu_ishtar), a copyright/work tag (e.g. yu-gi-oh!),
              or a general/descriptive tag (e.g. black_hair). Use Danbooru's
              canonical underscore form. A space form (e.g. "black hair") is
              accepted and normalized to underscores automatically. May be an
              EMPTY string when only --check is wanted.
    --limit  (required)              Number of SFW posts to sample, 1-200
              (Danbooru's per-page maximum). Recommended: 50 for a standard
              look, up to 200 for obscure characters or a deep census.
              Ignored in check-only mode.
    --verify (required)              Comma-separated list of specific tags whose
              exact usage you want confirmed (the tags you are considering for
              the prompt but are not sure Danbooru actually uses). Each is
              reported with its exact count and a verdict. Pass an EMPTY string
              ("" ) if you only want the general frequency report.
    --check  (optional)              Comma-separated list of EXACT tag names to
              existence-check (dictionary-level, independent of sampling).
              Each name is probed with posts.json?tags=<name>&limit=1 and
              reported as EXISTS (the name is carried literally by the matched
              post), ALIAS (the name resolves to real posts but the posts use a
              different canonical name; candidate canonical names are listed),
              or NOT FOUND (no posts match the name; it most likely does not
              exist -- express it in natural language). Pass an EMPTY string
              when not needed. Space-form names are auto-normalized.

Sampling model:
    Posts are fetched as the most-rated SFW posts matching the tag. The rating
    and ordering filters are embedded in the tags value as "rating:s order:score"
    (see fetch()) because the posts.json API ignores standalone rating/order
    query parameters. The most-rated posts are the best representatives of how a
    character is *canonically* drawn, so their tag distribution is a good proxy
    for the character's true identity. The report states whether the returned
    set is a complete census or a (top-rated) sample.

Output:
    A self-documenting Markdown report printed to stdout, with sections:
      - Summary                (tag, post count, census-vs-sample, sampling)
      - Warnings               (tag-not-found / small-sample, when applicable)
      - General / Character / Copyright / Meta  (ranked frequency tables)
      - Artist tags            (shown separately, flagged as "avoid in prompts")
      - Candidate verification (exact count + verdict for each --verify tag)
      - Tag existence check    (EXISTS / ALIAS / NOT FOUND per --check name)

IMPORTANT: --verify and --check answer different questions.
    --verify  : "is this tag common among the most-rated SFW posts carrying the
                analyzed tag?" (co-occurrence within a SAMPLE). An ABSENT
                verdict only means "not in this SFW sample" -- NSFW-centric tags
                (ahegao, masturbation, pussy_juice, ...) read ABSENT even when
                the tag is perfectly real. Use --verify for identity/vocabulary.
    --check   : "does this exact name resolve to real posts at all?" (dictionary
                level, sampling-independent). A NOT FOUND verdict is a strong
                signal the name does not exist (or has zero posts yet). Use
                --check to settle canonical spellings and catch invented tags.

Verdicts for a candidate tag (share = count / total_posts_sampled):
    share >= 30%      -> "adopt"    : well-supported, use as a tag
    5% .. 30%        -> "moderate" : sometimes used; consider tag or NL
    < 5% or absent   -> "rare/absent": prefer natural language
"""

import argparse
import json
import sys
import urllib.error
import urllib.parse
import urllib.request
from collections import Counter

API = "https://danbooru.donmai.us/posts.json"
USER_AGENT = "eca-danbooru-tags/1.0 (prompt-building helper)"

SMALL_SAMPLE = 10   # fewer posts than this -> warn that frequencies are low-confidence
ADOPT_TH = 0.30     # share >= this  -> adopt as a tag
MODERATE_TH = 0.05  # share in [this, ADOPT_TH) -> moderate; below this -> rare

# (json field suffix, report title, max rows to show)
CATEGORIES = [
    ("general",   "General / descriptive tags (appearance, clothing, scene)", 40),
    ("character", "Character tags", 15),
    ("copyright", "Copyright / work tags", 15),
    ("meta",      "Meta tags (count / image / render)", 15),
]

# Tags that carry no information about the character (resolution-source
# markers and the bare commentary flag); excluded from the report entirely.
IGNORE_NOISE = {"highres", "commentary", "lowres", "absurdres"}


def norm(tag):
    """Normalize a tag to Danbooru's canonical form (underscores, no spaces)."""
    return tag.strip().replace(" ", "_")


def http_get_json(url):
    """GET `url`, parse the response body as JSON and return it.

    Single HTTP seam for the whole script: tests monkeypatch this function to
    run fully offline, and every request goes through it (User-Agent, timeout
    and error behavior stay consistent).
    """
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(req, timeout=120) as resp:
        return json.loads(resp.read().decode("utf-8"))


def fetch(tag, limit):
    """Fetch SFW posts for `tag`, ranked by score. Returns
    (posts_list, normalized_tag, url).

    IMPORTANT (Danbooru quirk): the posts.json API does NOT honor standalone
    `rating=` / `order=` query parameters -- they are silently ignored. Rating
    and ordering filters must be embedded in the `tags` value as `name:value`
    pseudo-tags. So we build the tags string as "<tag> rating:s order:score".
      * `rating:s`   -> restrict to safe (SFW) posts only.
      * `order:score`-> rank by (up - down) score, surfacing the most-rated
                        (i.e. most canonically-drawn) posts first.
    """
    t = norm(tag)
    if not t:
        raise ValueError("empty tag")
    tags_value = "%s rating:s order:score" % t
    qs = urllib.parse.urlencode({"tags": tags_value, "limit": limit})
    url = "%s?%s" % (API, qs)
    posts = http_get_json(url)
    return posts, t, url


def check_name(name, limit=3):
    """Empirical existence probe for one exact tag name. Returns
    (posts_list, normalized_name, url).

    Queries posts.json with the bare name and a small limit. If at least one
    post is returned, the name is USABLE: it is either a canonical tag (the
    post carries it literally, see post_tag_set) or an alias of one (the
    search resolves the alias and the post carries the canonical name
    instead). An empty list means the name matches no post -- the tag most
    likely does not exist (or is a brand-new tag with zero posts).

    Why posts.json and not tags.json? The tags show endpoint and the
    tags.json name/name_matches filters are unreliable in practice (they
    404 / ignore parameters even for tags demonstrably in use); posts.json
    search is the stable ground truth this script already relies on.
    """
    n = norm(name)
    if not n:
        raise ValueError("empty check name")
    qs = urllib.parse.urlencode({"tags": n, "limit": limit})
    url = "%s?%s" % (API, qs)
    posts = http_get_json(url)
    return posts, n, url


def post_tag_set(post):
    """Return the set of all tag names carried by one post (every category)."""
    tags = set()
    for suffix in ("general", "character", "copyright", "meta", "artist"):
        for tg in (post.get("tag_string_" + suffix) or "").split():
            tags.add(tg)
    return tags


def alias_candidates(posts, name, cap=12):
    """Guess the canonical name(s) behind an alias.

    A search for an alias only returns posts that carry the canonical tag,
    so the tags shared by ALL matched posts are the strongest candidates.
    Returns a deterministic (sorted) list, capped at `cap` entries.
    """
    sets = [post_tag_set(p) for p in posts if isinstance(p, dict)]
    if not sets:
        return []
    common = set.intersection(*sets)
    common.discard(name)
    common -= IGNORE_NOISE
    return sorted(common)[:cap]


def render_check_section(names):
    """Build the '## Tag existence check' report lines for `names`.

    One posts.json probe per name; network errors on a single name are
    reported inline ([ERROR]) and do not abort the remaining names.
    """
    out = ["## Tag existence check"]
    for name in names:
        try:
            posts, n, url = check_name(name)
        except Exception as e:
            out.append("- `%s`  [ERROR] %r" % (name, e))
            continue
        if not posts:
            out.append("- `%s`  [NOT FOUND] no posts match this name -> the tag most likely "
                       "does not exist (or is a brand-new tag with zero posts); express the "
                       "concept in natural language or try a name variant. (query: %s)" % (n, url))
            continue
        if n in post_tag_set(posts[0]):
            out.append("- `%s`  [EXISTS] canonical tag: posts match the name and the matched "
                       "post literally carries it. (query: %s)" % (n, url))
        else:
            cands = alias_candidates(posts, n)
            cand_text = ", ".join("`%s`" % c for c in cands) if cands else "unknown"
            out.append("- `%s`  [ALIAS] the name resolves to real posts, but the posts use a "
                       "different canonical name; candidate canonical name(s) shared by all %d "
                       "matched post(s): %s. (query: %s)" % (n, len(posts), cand_text, url))
    out.append("")
    out.append("Note: EXISTS/ALIAS means the name resolves to real posts (a canonical tag or an "
               "alias of one); NOT FOUND is a strong signal, not absolute (a zero-post tag would "
               "also read NOT FOUND).")
    out.append("")
    return out


def count_tags(posts):
    """Build per-category tag Counters plus an artist Counter."""
    counters = {suffix: Counter() for suffix, _, _ in CATEGORIES}
    artist = Counter()
    for p in posts:
        for suffix, _, _ in CATEGORIES:
            for tg in (p.get("tag_string_" + suffix) or "").split():
                if tg in IGNORE_NOISE:
                    continue
                counters[suffix][tg] += 1
        for tg in (p.get("tag_string_artist") or "").split():
            artist[tg] += 1
    return counters, artist


def verdict(count, total):
    """Return (code, message) for a candidate tag given its count and the
    total number of sampled posts."""
    if total <= 0 or count == 0:
        return ("absent",
                "NOT FOUND in the sampled posts -> there is no (or no common) "
                "Danbooru tag for this; express it in natural language instead.")
    share = count / total
    if share >= ADOPT_TH:
        return ("adopt",
                "well-supported (%d/%d, %.0f%%) -> adopt as a tag." % (count, total, share * 100))
    if share >= MODERATE_TH:
        return ("moderate",
                "moderate (%d/%d, %.0f%%) -> may be a tag or NL; confirm against "
                "official sources before relying on it." % (count, total, share * 100))
    return ("rare",
            "rare (%d/%d, %.0f%%) -> prefer natural language over a tag." % (count, total, share * 100))


def render_table(counter, total, n):
    """Render the top-n rows of a Counter as aligned text lines."""
    lines = []
    for rank, (tg, c) in enumerate(counter.most_common(n), 1):
        lines.append("%3d. %-34s %4d/%-4d (%5.0f%%)" % (rank, tg, c, total, c / total * 100))
    return lines


def describe_population(total, limit):
    """Human-readable description of whether we have a census or a sample."""
    if total < limit:
        return "complete census (all %d matching SFW posts returned; fewer than the requested limit)" % total
    if limit >= 200:
        return "top-%d by rating (Danbooru caps a request at 200; the true total may be larger)" % limit
    return "sample of the top-%d most-rated posts (raise --limit for a fuller census)" % limit


def build_analysis_report(posts, ntag, url, limit, verify_names):
    """Build the analysis-mode report lines (the established format).

    `posts` is the (possibly empty) list returned by fetch(); `verify_names`
    is the parsed --verify candidate list. Returns a list of lines ready for
    "\\n".join + print.
    """
    total = len(posts)

    # ---- Tag not found ----
    if total == 0:
        return [
            "# Danbooru Tag Analysis: %s\n" % ntag,
            "## Summary",
            "- Tag: `%s`" % ntag,
            "- SFW posts matched: **0**",
            "- Query: %s" % url,
            "\n## WARNING: TAG NOT FOUND",
            "No SFW posts matched `%s`. The tag most likely does not exist on" % ntag,
            "Danbooru, is misspelled, or is far too obscure to have any art.",
            "Check the tag against the Danbooru tag index or a reference image,",
            "and express the concept in natural language instead.",
        ]

    counters, artist = count_tags(posts)

    # ---- Build report ----
    out = []
    out.append("# Danbooru Tag Analysis: %s\n" % ntag)

    out.append("## Summary")
    out.append("- Tag: `%s`" % ntag)
    out.append("- Population: %s" % describe_population(total, limit))
    out.append("- Sampling: rating=safe, order=score (most-rated SFW posts)")
    out.append("- Distinct tags: general=%d, character=%d, copyright=%d, meta=%d, artist=%d"
               % (len(counters["general"]), len(counters["character"]),
                  len(counters["copyright"]), len(counters["meta"]), len(artist)))
    out.append("- Query: %s" % url)
    out.append("")

    if total < SMALL_SAMPLE:
        out.append("## WARNING")
        out.append("- Small sample (%d posts). Frequency percentages are low-confidence;"
                    " cross-check against official sources and reference images before"
                    " adopting any tag." % total)
        out.append("")

    # Ranked frequency tables per category
    for suffix, title, maxrows in CATEGORIES:
        c = counters[suffix]
        if not c:
            continue
        out.append("## %s" % title)
        rows = render_table(c, total, maxrows)
        if not rows:
            continue
        out.extend(rows)
        if len(c) > maxrows:
            out.append("... (%d distinct total; top %d shown)" % (len(c), maxrows))
        out.append("")

    # Artist tags: shown for awareness, flagged as "avoid"
    if artist:
        top = ", ".join(t for t, _ in artist.most_common(3))
        out.append("## Artist tags (generally AVOID in a character prompt)")
        out.append("%d distinct artist tag(s); most common: %s." % (len(artist), top))
        out.append("Artist tags bias the output toward a specific artist's style, so exclude")
        out.append("them unless you are intentionally matching that artist.")
        out.append("")

    # Candidate verification
    if verify_names:
        # Merge counts across the meaningful categories for lookup.
        lookup = Counter()
        for suffix, _, _ in CATEGORIES:
            for tg, c in counters[suffix].items():
                lookup[tg] += c
        out.append("## Candidate tag verification")
        for v in verify_names:
            canon = norm(v)
            count = lookup.get(canon, 0)
            if count == 0:
                count = lookup.get(v, 0)  # fallback: raw form, in case it was already underscored
            code, msg = verdict(count, total)
            mark = {"adopt": "[ADOPT]", "moderate": "[MODERATE]",
                    "rare": "[RARE]", "absent": "[ABSENT]"}[code]
            out.append("- `%s`  %s %s" % (v, mark, msg))
        out.append("")

    return out


def main():
    ap = argparse.ArgumentParser(
        description="Analyze Danbooru tag usage and check tag existence for prompt building.")
    ap.add_argument("tag", nargs="?", default="",
                    help="Danbooru tag to analyze (character/work/general); "
                         "pass an empty string when only --check is wanted.")
    ap.add_argument("--limit", type=int, required=True,
                    help="Number of SFW posts to sample (1-200); ignored in check-only mode.")
    # nargs="?" so the flag tolerates an EMPTY value: shells (and ECA's command
    # template) may drop a quoted empty-string argument, leaving "--verify" with
    # no value. nargs="?" + default makes argparse fall back to "" in that case
    # instead of raising "expected one argument".
    # const="" handles the "flag present but value dropped by the shell" case;
    # default="" handles the "flag absent" case. Both must be "" for robustness.
    ap.add_argument("--verify", nargs="?", const="", default="",
                    help="Comma-separated candidate tags to verify against the sampled "
                         "posts (ADOPT/MODERATE/RARE/ABSENT verdicts); empty for the "
                         "general report only.")
    ap.add_argument("--check", nargs="?", const="", default="",
                    help="Comma-separated exact tag names to existence-check "
                         "(EXISTS/ALIAS/NOT FOUND); independent of sampling, works "
                         "standalone with an empty tag; empty when not needed.")
    args = ap.parse_args()

    check_names = [c.strip() for c in args.check.replace(";", ",").split(",") if c.strip()]
    do_analysis = bool(args.tag.strip())
    if not do_analysis and not check_names:
        print("Error: either the tag or --check must be non-empty.", file=sys.stderr)
        sys.exit(1)
    if do_analysis and not 1 <= args.limit <= 200:
        print("Error: --limit must be between 1 and 200.", file=sys.stderr)
        sys.exit(1)

    out = []

    # ---- Analysis mode (post sampling + co-occurrence report) ----
    if do_analysis:
        try:
            posts, ntag, url = fetch(args.tag, args.limit)
        except urllib.error.HTTPError as e:
            print("HTTP Error %s: %s" % (e.code, e.reason), file=sys.stderr)
            try:
                print("Details: %s" % json.loads(e.read().decode("utf-8")), file=sys.stderr)
            except Exception:
                pass
            sys.exit(1)
        except urllib.error.URLError as e:
            print("Connection error: %s" % (e.reason,), file=sys.stderr)
            sys.exit(1)
        except ValueError as e:
            print("Error: %s" % (e,), file=sys.stderr)
            sys.exit(1)
        except Exception as e:
            print("Unexpected error: %r" % (e,), file=sys.stderr)
            sys.exit(1)

        if not isinstance(posts, list):
            print("Error: unexpected API response (expected a JSON list of posts).", file=sys.stderr)
            sys.exit(1)

        verify_names = [v.strip() for v in args.verify.replace(";", ",").split(",") if v.strip()]
        out = build_analysis_report(posts, ntag, url, args.limit, verify_names)
    else:
        out = [
            "# Danbooru Tag Check (existence verification)",
            "",
            "## Summary",
            "- Mode: check-only (no post sampling; --limit/--verify ignored)",
            "- Names checked: %d" % len(check_names),
            "",
        ]

    # ---- Tag existence check (appended in both modes) ----
    if check_names:
        out.extend(render_check_section(check_names))

    print("\n".join(out))


if __name__ == "__main__":
    main()

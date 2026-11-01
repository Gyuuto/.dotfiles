"""Specification tests for tools/read_image.py.

All tests run OFFLINE: the single HTTP seam ``http_get_json`` is monkeypatched
and the session resolution reads fixtures from a temp cache/config instead of
the real ``~/.cache/eca`` and ``~/.config/eca``.

The spec under test is the module docstring of ``read_image.py``: endpoint
resolution order (env override -> ECA session -> DEFAULT_SERVER_BASE), the
chat-state model lookup, URL building, and model selection.

Run with:
    python -m pytest tools/tests
"""
import json
import sys
from pathlib import Path

import pytest

# Make tools/ importable as a top-level package root regardless of the cwd.
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import read_image as ri  # noqa: E402


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

CHAT_ID = "c8d8da1b-493d-4fbf-b042-3bc56fca012c"
SESSION_MODEL = "home-server-strata/qwen3.8-flash-next-iq2_xs"
STRATA_URL = "http://192.168.50.3:8080/v1"
LLAMA_URL = "http://192.168.50.3:11434"


def write_config(tmp_path):
    """JSONC config fixture, with a // comment that contains a URL."""
    cfg = tmp_path / "config.json"
    cfg.write_text(
        '{\n'
        '  "providers": {\n'
        '    "home-server-llama": { "url": "%s", "key": "TERM" },\n'
        '    "home-server-strata": { "url": "%s", "key": "session-key" } // see %s\n'
        '  }\n'
        '}' % (LLAMA_URL, STRATA_URL, LLAMA_URL),
        encoding="utf-8",
    )
    return cfg


def write_chat_file(tmp_path, chat_id, model):
    """Minimal chat state file as ECA writes it (transit-encoded JSON)."""
    chats = tmp_path / "cache" / "eca_paPXj3Av" / "chats"
    chats.mkdir(parents=True)
    record = '["^ ", "~:version", 7, "~:chat", ["^ ", "~:title", "t", "~:model", "%s"]]' % model
    (chats / (chat_id + ".transit.json")).write_text(record, encoding="utf-8")
    return tmp_path / "cache"


# ---------------------------------------------------------------------------
# JSONC parsing (config.json allows // comments)
# ---------------------------------------------------------------------------

def test_strip_json_comments_removes_line_comments():
    text = '{\n  "a": 1, // note\n  "b": 2\n}'
    assert json.loads(ri.strip_json_comments(text)) == {"a": 1, "b": 2}


def test_strip_json_comments_keeps_double_slash_inside_strings():
    text = '{"url": "http://example.com:8080/v1"} // http://comment'
    assert json.loads(ri.strip_json_comments(text)) == {"url": "http://example.com:8080/v1"}


def test_load_config_reads_provider_url_and_key(tmp_path):
    config = ri.load_config(write_config(tmp_path))
    assert config["providers"]["home-server-strata"]["url"] == STRATA_URL
    assert config["providers"]["home-server-strata"]["key"] == "session-key"


# ---------------------------------------------------------------------------
# Chat state lookup
# ---------------------------------------------------------------------------

def test_extract_chat_model_reads_the_record_value():
    record = '["^ ", "~:version", 7, "~:chat", ["^ ", "~:title", "t", "~:model", "%s"]]' % SESSION_MODEL
    assert ri.extract_chat_model(record) == SESSION_MODEL


def test_extract_chat_model_ignores_the_word_in_message_content():
    record = '["^ ", "~:chat", ["^ ", "~:messages", [["^ ", "~:content", "text mentioning ~:model"]]]]'
    assert ri.extract_chat_model(record) is None


def test_find_chat_file_resolves_the_workspace_hash_dir(tmp_path):
    cache = write_chat_file(tmp_path, CHAT_ID, SESSION_MODEL)
    found = ri.find_chat_file(CHAT_ID, cache)
    assert found is not None and found.name == CHAT_ID + ".transit.json"
    assert ri.find_chat_file("no-such-chat", cache) is None


# ---------------------------------------------------------------------------
# Endpoint resolution order
# ---------------------------------------------------------------------------

def test_session_env_resolves_provider_url_from_config(tmp_path):
    cache = write_chat_file(tmp_path, CHAT_ID, SESSION_MODEL)
    target = ri.resolve_session_target({"ECA_CHAT_ID": CHAT_ID}, cache, write_config(tmp_path))
    assert target["base"] == STRATA_URL
    assert target["key"] == "session-key"
    assert target["model"] == SESSION_MODEL
    assert target["source"].startswith("ECA session")


def test_env_override_wins_over_the_session(tmp_path):
    cache = write_chat_file(tmp_path, CHAT_ID, SESSION_MODEL)
    target = ri.resolve_session_target(
        {"ECA_CHAT_ID": CHAT_ID, "ECA_READ_IMAGE_SERVER": "http://127.0.0.1:9999"},
        cache, write_config(tmp_path),
    )
    assert target["base"] == "http://127.0.0.1:9999"
    assert target["source"] == "ECA_READ_IMAGE_SERVER override"


def test_falls_back_to_default_without_chat_id(tmp_path):
    target = ri.resolve_session_target({}, tmp_path / "cache", write_config(tmp_path))
    assert target["base"] == ri.DEFAULT_SERVER_BASE
    assert target["key"] == ri.DEFAULT_KEY
    assert target["model"] is None
    assert "no ECA_CHAT_ID" in target["source"]


def test_falls_back_when_chat_state_file_is_missing(tmp_path):
    target = ri.resolve_session_target({"ECA_CHAT_ID": CHAT_ID},
                                      tmp_path / "cache", write_config(tmp_path))
    assert target["base"] == ri.DEFAULT_SERVER_BASE
    assert "chat state file not found" in target["source"]


def test_falls_back_when_provider_is_not_in_config(tmp_path):
    cache = write_chat_file(tmp_path, CHAT_ID, "unknown-provider/some-model")
    target = ri.resolve_session_target({"ECA_CHAT_ID": CHAT_ID}, cache, write_config(tmp_path))
    assert target["base"] == ri.DEFAULT_SERVER_BASE
    assert "not in config.json" in target["source"]
    # the provider URL is unknown, so no model id can be used against the fallback endpoint
    assert target["model"] is None


def test_extract_chat_model_returns_none_for_reference_values():
    record = '["^ ", "~:chat", ["^ ", "~:model", "^?"]]'
    assert ri.extract_chat_model(record) is None


def test_falls_back_when_the_model_is_a_transit_reference(tmp_path):
    cache = write_chat_file(tmp_path, CHAT_ID, "^?")
    target = ri.resolve_session_target({"ECA_CHAT_ID": CHAT_ID}, cache, write_config(tmp_path))
    assert target["base"] == ri.DEFAULT_SERVER_BASE
    assert "no literal model" in target["source"]


def test_resolve_session_target_honours_eca_config_env(tmp_path):
    cache = write_chat_file(tmp_path, CHAT_ID, SESSION_MODEL)
    target = ri.resolve_session_target(
        {"ECA_CHAT_ID": CHAT_ID, "ECA_CONFIG": str(write_config(tmp_path))}, cache)
    assert target["base"] == STRATA_URL


# ---------------------------------------------------------------------------
# URL building and model selection
# ---------------------------------------------------------------------------

def test_api_url_appends_v1_when_base_has_no_path():
    assert ri.api_url(LLAMA_URL, "chat/completions") == LLAMA_URL + "/v1/chat/completions"
    assert ri.api_url(LLAMA_URL + "/", "models") == LLAMA_URL + "/v1/models"


def test_api_url_does_not_duplicate_v1_when_base_already_ends_with_v1():
    assert ri.api_url(STRATA_URL, "chat/completions") == STRATA_URL + "/chat/completions"
    assert ri.api_url(STRATA_URL, "models") == STRATA_URL + "/models"


def test_strip_variant_removes_the_variant_suffix():
    assert ri.strip_variant("provider/model:REASONING_MEDIUM") == "provider/model"
    assert ri.strip_variant("provider/model") == "provider/model"


def test_select_model_prefers_the_loaded_model():
    target = {"base": LLAMA_URL, "key": "TERM", "model": SESSION_MODEL}
    model, error = ri.select_model(target, ["loaded/model"])
    assert model == "loaded/model" and error is None


def test_select_model_falls_back_to_the_session_model_variant_stripped():
    target = {"base": STRATA_URL, "key": "TERM", "model": "home-server-strata/m:REASONING_MEDIUM"}
    model, error = ri.select_model(target, [])
    assert model == "home-server-strata/m" and error is None


def test_select_model_errors_on_multiple_loaded_models():
    target = {"base": LLAMA_URL, "key": "TERM", "model": SESSION_MODEL}
    model, error = ri.select_model(target, ["a/model", "b/model"])
    assert model is None and "multiple models" in error


def test_select_model_errors_when_nothing_is_known():
    target = {"base": LLAMA_URL, "key": "TERM", "model": None}
    model, error = ri.select_model(target, [])
    assert model is None and "no model is loaded" in error


def test_resolve_loaded_models_reports_only_loaded_entries(monkeypatch):
    monkeypatch.setattr(ri, "http_get_json", lambda url, key: {
        "data": [
            {"id": "loaded/model", "status": {"value": "loaded"}},
            {"id": "not-loaded/model", "status": {"value": " unloaded"}},
            {"id": "no-status/model"},
        ]
    })
    assert ri.resolve_loaded_models(LLAMA_URL, "TERM") == ["loaded/model"]


def test_resolve_loaded_models_returns_empty_for_providers_without_status(monkeypatch):
    monkeypatch.setattr(ri, "http_get_json", lambda url, key: {"data": [{"id": "x/model"}]})
    assert ri.resolve_loaded_models(STRATA_URL, "TERM") == []

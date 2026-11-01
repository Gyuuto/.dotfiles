#!/usr/bin/env python3
"""
Read an image file and send it to the LLM API endpoint of the current ECA
session with a prompt. Returns the model's response about the image content.

Thinking is disabled via chat_template_kwargs (enable_thinking: false): the
model answers directly. On thinking models the thinking phase alone can
consume the whole output budget, leaving an empty content (the tool then
prints None); direct perception questions do not need thinking.

Usage:
    python3 read_image.py <image_path> <prompt>

Arguments:
    image_path: Absolute path to the image file
    prompt: Text prompt/question about the image

Endpoint resolution, in order:
    1. ECA_READ_IMAGE_SERVER env var (explicit override).
    2. The current ECA session. ECA sets ECA_CHAT_ID for every command it
       spawns; the chat state file
       ~/.cache/eca/<workspace-hash>/chats/<chat-id>.transit.json records the
       chat's model as "<provider>/<model>", and that provider's url and key
       are then looked up in ~/.config/eca/config.json.
    3. DEFAULT_SERVER_BASE, used when the session cannot be resolved (e.g. the
       script is run manually, outside an ECA chat).

Resolution is done per call (nothing is cached), so a model switch in the chat
is followed on the next call. Values the chat state file writes as transit
references are not resolved; the script falls back in that case.

The model to call is auto-detected from the endpoint via GET /v1/models
(entries whose status.value is "loaded"); when the endpoint does not report
loaded models, the model recorded for the session is used instead.
"""

import base64
import json
import os
import re
import sys
import urllib.request
import urllib.error
from pathlib import Path

DEFAULT_SERVER_BASE = "http://192.168.50.3:11434"
DEFAULT_KEY = "TERM"

# The chat state file is transit-encoded JSON; the chat record stores the model
# as a literal "<provider>/<model>" string under the ~:model key.
CHAT_MODEL_RE = re.compile(r'"~:model"\s*,\s*"([^"]+)"')


def strip_json_comments(text):
    """Strip // comments from JSONC text, leaving // inside strings intact."""
    out = []
    i = 0
    in_string = False
    while i < len(text):
        char = text[i]
        if in_string:
            if char == "\\":
                out.append(text[i:i + 2])
                i += 2
                continue
            if char == '"':
                in_string = False
            out.append(char)
            i += 1
            continue
        if char == '"':
            in_string = True
            out.append(char)
            i += 1
            continue
        if char == "/" and text[i + 1:i + 2] == "/":
            while i < len(text) and text[i] != "\n":
                i += 1
            continue
        out.append(char)
        i += 1
    return "".join(out)


def load_config(path):
    """Parse ECA config.json (JSONC: // comments are allowed)."""
    return json.loads(strip_json_comments(Path(path).read_text(encoding="utf-8")))


def find_chat_file(chat_id, cache_dir):
    """Path of the chat state file for chat_id inside the ECA cache dir."""
    for path in Path(cache_dir).glob("*/chats/" + chat_id + ".transit.json"):
        return path
    return None


def extract_chat_model(text):
    """The "<provider>/<model>" the chat state file records for this chat.

    Returns None when the value is a transit reference (a repeated string)
    rather than a literal; references are not resolved here.
    """
    match = CHAT_MODEL_RE.search(text)
    if not match:
        return None
    value = match.group(1)
    return None if value.startswith("^") else value


def strip_variant(model_id):
    """Drop the ":VARIANT" suffix an ECA model id may carry."""
    return model_id.rsplit(":", 1)[0]


def api_url(base, path):
    """Absolute API URL; handles provider urls that already end with /v1."""
    base = base.rstrip("/")
    if base.endswith("/v1"):
        return base + "/" + path
    return base + "/v1/" + path


def resolve_session_target(env=None, cache_dir=None, config_path=None):
    """Resolve the endpoint to send to for the current ECA session.

    Returns {"base", "key", "model", "source"}; "model" is the session model id
    (None when the session cannot be resolved), "source" explains where the
    endpoint came from. Falls back to DEFAULT_SERVER_BASE.
    """
    env = os.environ if env is None else env
    fallback = {"base": DEFAULT_SERVER_BASE, "key": DEFAULT_KEY, "model": None}

    override = env.get("ECA_READ_IMAGE_SERVER")
    if override:
        return dict(fallback, base=override,
                    key=env.get("ECA_READ_IMAGE_KEY", DEFAULT_KEY),
                    source="ECA_READ_IMAGE_SERVER override")

    chat_id = env.get("ECA_CHAT_ID")
    if not chat_id:
        return dict(fallback, source="no ECA_CHAT_ID (not run from an ECA chat)")

    cache_dir = Path.home() / ".cache" / "eca" if cache_dir is None else Path(cache_dir)
    if config_path is None:
        config_path = env.get("ECA_CONFIG") or (Path.home() / ".config" / "eca" / "config.json")
    config_path = Path(config_path)

    chat_file = find_chat_file(chat_id, cache_dir)
    if not chat_file:
        return dict(fallback, source="chat state file not found in ECA cache")

    session_model = extract_chat_model(chat_file.read_text(encoding="utf-8"))
    if not session_model:
        return dict(fallback, source="chat state file records no literal model")

    provider_name = session_model.split("/", 1)[0]
    try:
        config = load_config(config_path)
    except (OSError, json.JSONDecodeError):
        return dict(fallback, source="config.json unreadable")

    provider = config.get("providers", {}).get(provider_name)
    if not provider or not provider.get("url"):
        return dict(fallback, source="provider '" + provider_name + "' not in config.json")

    return {"base": provider["url"], "key": provider.get("key") or DEFAULT_KEY,
            "model": session_model, "source": "ECA session (" + provider_name + ")"}


def http_get_json(url, key):
    """Single HTTP seam: GET a JSON document."""
    req = urllib.request.Request(url, headers={"Authorization": "Bearer " + key})
    with urllib.request.urlopen(req, timeout=30) as response:
        return json.loads(response.read().decode("utf-8"))


def resolve_loaded_models(base, key):
    """Query the endpoint for the models currently loaded in memory.

    llama.cpp reports the full model catalog; only entries whose status.value is
    "loaded" are returned (typically exactly one). Other OpenAI-compatible
    providers report no status, so this returns an empty list.
    """
    data = http_get_json(api_url(base, "models"), key)
    loaded = []
    for m in data.get("data", []):
        status = m.get("status")
        if isinstance(status, dict) and status.get("value") == "loaded":
            loaded.append(m["id"])
    return loaded


def select_model(target, loaded):
    """Pick the model id to call: the loaded model, else the session model.

    Returns (model, error); error is None on success.
    """
    if len(loaded) == 1:
        return loaded[0], None
    if len(loaded) > 1:
        return None, ("multiple models are loaded on the endpoint; load exactly one:\n  "
                      + "\n  ".join(loaded))
    if target.get("model"):
        return strip_variant(target["model"]), None
    return None, "no model is loaded on the endpoint and no session model is known"


def main():
    if len(sys.argv) != 3:
        print("Usage: python3 read_image.py <image_path> <prompt>", file=sys.stderr)
        sys.exit(1)

    image_path = sys.argv[1]
    prompt = sys.argv[2]

    target = resolve_session_target()
    print(f"endpoint: {target['base']} ({target['source']})", file=sys.stderr)
    server_url = api_url(target["base"], "chat/completions")

    # Prefer the model currently loaded on the endpoint; fall back to the model
    # the current session uses when the endpoint reports no loaded models.
    try:
        loaded = resolve_loaded_models(target["base"], target["key"])
    except urllib.error.HTTPError as e:
        print(f"HTTP Error {e.code}: {e.reason} (while resolving loaded model; "
              "falling back to the session model)", file=sys.stderr)
        loaded = []
    except urllib.error.URLError as e:
        print(f"Connection error: {e.reason} (while resolving loaded model)", file=sys.stderr)
        sys.exit(1)

    model, error = select_model(target, loaded)
    if error:
        print("Error: " + error, file=sys.stderr)
        sys.exit(1)

    # Read and encode image
    try:
        with open(image_path, "rb") as f:
            image_data = f.read()
    except FileNotFoundError:
        print(f"Error: Image file not found: {image_path}", file=sys.stderr)
        sys.exit(1)
    except PermissionError:
        print(f"Error: Permission denied reading: {image_path}", file=sys.stderr)
        sys.exit(1)

    image_b64 = base64.b64encode(image_data).decode("utf-8")

    # Build request payload
    payload = {
        "model": model,
        "messages": [
            {
                "role": "user",
                "content": [
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:image/png;base64,{image_b64}"
                        }
                    },
                    {
                        "type": "text",
                        "text": prompt
                    }
                ]
            }
        ],
        "max_tokens": 4096,
        "temperature": 0.6,
        "chat_template_kwargs": {"enable_thinking": False},
        "stream": False
    }

    # Send request
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        server_url,
        data=data,
        headers={
            "Content-Type": "application/json",
            "Authorization": "Bearer " + target["key"]
        }
    )

    try:
        with urllib.request.urlopen(req, timeout=600) as response:
            result = json.loads(response.read().decode("utf-8"))
            print(result["choices"][0]["message"]["content"])
    except urllib.error.HTTPError as e:
        print(f"HTTP Error {e.code}: {e.reason}", file=sys.stderr)
        try:
            error_body = json.loads(e.read().decode("utf-8"))
            print(f"Details: {json.dumps(error_body, ensure_ascii=False)}", file=sys.stderr)
        except Exception:
            pass
        sys.exit(1)
    except urllib.error.URLError as e:
        print(f"Connection error: {e.reason}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()

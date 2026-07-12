# Custom Tools Documentation

## Overview

ECA custom tools for web search and content fetching, configured in `config.json` under the `customTools` key.

## Tools

### web-search

Searches the web using DuckDuckGo and returns results as JSON.

- **Command:** `python3 -c "from ddgs import DDGS; import json,sys; print(json.dumps(DDGS().text('{{query}}', max_results=5), ensure_ascii=False))"`
- **Package:** `ddgs` (PyPI)
- **Output:** JSON array of `{title, href, body}` objects
- **Use case:** Finding information about unknown topics, getting latest information

### web-fetch

Fetches a URL and returns its content as Markdown.

- **Command:** `trafilatura --output-format=markdown -u "{{url}}"`
- **Package:** `trafilatura` (PyPI)
- **Output:** Markdown-formatted page content (boilerplate removed)
- **Use case:** Reading full content of pages found via web-search

### web-news

Searches recent news using DuckDuckGo and returns results as JSON.

- **Command:** `ddgs news -o json -m 5 -q "{{query}}"`
- **Package:** `ddgs` (PyPI)
- **Output:** JSON array of news results
- **Use case:** Getting the latest news about a topic

## Installation

```bash
pip install ddgs trafilatura
```

After installation, verify the CLI flags:

```bash
ddgs text --help
ddgs news --help
trafilatura --help
```

If the CLI flags differ from the configured commands, update the `command` strings in `config.json` accordingly.

## Usage Workflow

```
Unknown concept / latest info needed
  → web-search("topic name")
    → Get list of relevant URLs
      → web-fetch("https://...") to read content

Latest news needed
  → web-news("topic name")
    → Get recent news articles
```

## Security Considerations

### Execution Mechanism (Investigated from ECA v0.145.0 binary)

ECA executes custom tool commands via `java.lang.ProcessBuilder` (babashka.process), **not via shell** (`sh -c`). This means:

- **Shell injection is NOT possible.** Metacharacters like `;`, `|`, `&&`, `$()`, `` ` ``, `>`, `<` are treated as literal characters, not shell operators.
- **HTML escaping is disabled** for command rendering (Selmer `without-escaping`), so URLs with `&` are passed correctly.

### Argument Handling

1. Selmer substitutes `{{arg}}` with the LLM-provided value (no escaping)
2. The result is tokenized (space-split, quote-aware) into an argument array
3. The argument array is passed to ProcessBuilder directly

### Quoting Strategy

Arguments are wrapped in double quotes (`"{{arg}}"`) in the command string to prevent space-splitting of multi-word values (e.g., search queries with spaces). The tokenizer recognizes `"` as a quote delimiter, so `"rust async traits"` becomes a single argument `rust async traits`.

### Known Limitations

- **Argument injection via quotes:** If the LLM-provided value contains `"`, it can break the quoting and affect tokenization. This is a low-risk scenario for LLM-generated queries, which rarely contain raw double quotes.
- **No argument escaping:** ECA does not apply shell or tokenizer-level escaping to LLM-provided values. This is by design — the command author is responsible for safe quoting.
- **DuckDuckGo censorship/bias:** DuckDuckGo may filter or down-rank certain results (e.g., Russian state media). Japanese search quality is lower than Google. Cross-check with multiple sources for sensitive topics.

## Dependencies

| Package | Purpose | Notes |
|---------|---------|-------|
| `ddgs` | DuckDuckGo search CLI | API key not required |
| `trafilatura` | Web content extraction | Outputs Markdown; removes boilerplate |

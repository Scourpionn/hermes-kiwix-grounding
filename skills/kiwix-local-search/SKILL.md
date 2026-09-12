# Kiwix local search

Use this skill to ground factual answers in a local Kiwix Server before using the public Internet.

## Purpose

Kiwix serves downloadable ZIM archives (for example, an offline Wikipedia snapshot) over a local HTTP server. It is useful when Internet access is unavailable, unreliable, expensive, or deliberately kept out of the first research step.

For an external factual question, run the helper once before answering when a local Kiwix source is relevant. Do not make this dependent on the model selecting a tool.

## Required lookup

Run exactly one helper command with the absolute installed path:

```bash
python3 /opt/data/profiles/default/skills/research/kiwix-local-search/scripts/search_kiwix.py "<short canonical subject>"
```

Examples:

```bash
python3 /opt/data/profiles/default/skills/research/kiwix-local-search/scripts/search_kiwix.py "Victor Hugo"
python3 /opt/data/profiles/default/skills/research/kiwix-local-search/scripts/search_kiwix.py "Paris Eiffel Tower"
python3 /opt/data/profiles/default/skills/research/kiwix-local-search/scripts/search_kiwix.py "Nepal landslide"
```

The helper removes surrounding prompt scaffolding, normalizes whitespace, and performs at most one conservative fuzzy correction. It also handles common French Wikipedia aliases. Do not inspect the helper source or parse Kiwix with `grep`, `curl`, a browser, or another intermediate workflow. Do not issue multiple phrasings if the first call returns a usable result.

## Interpreting the result

- `status: ok`: use only the returned `article_text` for stable factual claims. Cite the selected local title and URL as the local source.
- `status: no_match`, `article_empty`, `article_error`, or `unreachable`: explain that the local source did not provide usable evidence, then use the Internet and open a current, primary or institutional source. Do not treat search snippets as evidence.
- If the result is clearly unrelated, make at most one second call with a shorter canonical subject. If it is still unrelated, move to the Internet fallback.

For changing information (news, prices, software versions, availability, laws, regulations, or current office holders), use Kiwix first when it can provide useful background, then verify the current state on the Internet with an authoritative source.

For a follow-up question about the same subject, reuse the existing `article_text` instead of running Kiwix again unless the user asks for a different subject.

Greetings, casual conversation, creative writing, and purely local code questions do not require a Kiwix lookup.

## Configuration

The helper reads these environment variables:

| Variable | Default | Meaning |
| --- | --- | --- |
| `KIWIX_URL` | `http://localhost:8091` | Kiwix Server base URL |
| `KIWIX_LANG` | `fra` | Preferred language/alias |
| `KIWIX_LIMIT` | `6` | Maximum search results |
| `KIWIX_MAX_CHARS` | `4500` | Maximum returned article characters |

Set `KIWIX_URL` to the address reachable from the Hermes runtime. For a NAS, use its LAN or overlay-network address instead of `localhost`.

## Source and fallback policy

Kiwix is a local evidence source, not a guarantee that every question is covered. If the requested fact is absent or potentially outdated, always continue with an Internet lookup. The final answer should distinguish local Kiwix evidence, current web verification, and anything that remains unverified.

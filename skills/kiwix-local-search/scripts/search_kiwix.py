#!/usr/bin/env python3
"""One-shot Kiwix lookup: search, select, fetch, and clean an article."""
from __future__ import annotations

import argparse, difflib, html, json, os, re, unicodedata, urllib.parse, urllib.request
import xml.etree.ElementTree as ET
from html.parser import HTMLParser

STOP = {
    "a", "ai", "aimerais", "achete", "au", "aux", "avec", "c", "ca", "ce", "ces", "comment", "cree", "creer", "d", "dans",
    "de", "des", "dessus", "developpe", "dire", "dit", "donne", "donner", "du", "elle", "en", "est", "et", "etait", "fondateur",
    "fondatrice", "fondateurs", "fais", "faire", "biographie", "il", "information", "informations", "la", "le", "les", "lui", "par", "parle", "peux", "phrase", "pour", "propos",
    "j", "leurs", "lors", "merci", "moi", "passe", "passee", "qu", "quand", "que", "quel", "quelle", "qui", "quoi", "raconte", "recherche", "rechercher", "cherchais", "cherche", "chercher", "renseigne", "renseigner", "renseignement", "s", "sais", "savoir", "sest", "ses", "spec", "specs", "stp", "svp", "sur", "te", "tu", "un", "une", "voudrais",
    "about", "created", "creator", "developed", "did", "founded", "founder", "is", "me",
    "of", "please", "tell", "the", "was", "what", "when", "where", "which", "who",
}

# Common names whose French Wikipedia article uses a different canonical title.
# Keys are accent-insensitive because norm() is applied before lookup.
ALIASES = {
    "napoleon": "Napoléon Ier",
    "napoleon bonaparte": "Napoléon Ier",
    "bonaparte": "Napoléon Ier",
    "victor hugo biographie": "Victor Hugo",
    "biographie victor hugo": "Victor Hugo",
    "prise bastille": "Prise de la Bastille",
    "bastille": "Prise de la Bastille",
}


def norm(value: str) -> str:
    value = unicodedata.normalize("NFKD", html.unescape(value))
    value = "".join(c for c in value if not unicodedata.combining(c))
    return " ".join(re.findall(r"[a-z0-9]+", value.lower()))


def words(value: str) -> set[str]:
    return {word for word in norm(value).split() if word not in STOP}


def canonical_subject(value: str) -> str:
    """Remove common question scaffolding while preserving the named subject."""
    # The automatic grounding hook receives the user's full message. Remove an
    # explicit trailing routing instruction ("utilise Kiwix stp") without
    # treating the word Kiwix itself as a stop-word: questions *about* Kiwix
    # must continue to search for the Kiwix article.
    value = re.sub(
        r"\s*[?.,;:!—-]*\s*(?:utilise|utiliser|avec|via)\s+(?:le\s+)?kiwix"
        r"(?:\s+(?:stp|svp))?[.!?]*\s*$",
        "", value, flags=re.IGNORECASE,
    )
    # Strip request verbs in their conversational context, not inside titles
    # such as "Trouver Forrester" or the magazine "Oui".
    value = re.sub(
        r"^\s*(?:(?:oui|ok|okay)[,\s]+)?(?:est[- ]ce\s+que\s+)?"
        r"(?:tu\s+peux|vous\s+pouvez|peux[- ]tu|pouvez[- ]vous)\s+"
        r"(?:(?:me|nous)\s+)?(?:trouver|chercher|rechercher)\s+",
        "", value, flags=re.IGNORECASE,
    )
    original = re.findall(r"[\wÀ-ÿ'-]+", value, flags=re.UNICODE)
    kept = [token for token in original if any(part not in STOP for part in norm(token).split())]
    subject = " ".join(kept).strip() or value.strip()
    return ALIASES.get(norm(subject), subject)


class TextExtractor(HTMLParser):
    BLOCKS = {"h1", "h2", "p", "li"}
    SKIP = {"script", "style", "nav", "header", "footer", "svg", "noscript"}

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.skip = 0
        self.block: str | None = None
        self.buffer: list[str] = []
        self.blocks: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag in self.SKIP:
            self.skip += 1
        elif not self.skip and tag in self.BLOCKS and self.block is None:
            self.block, self.buffer = tag, []

    def handle_endtag(self, tag: str) -> None:
        if tag in self.SKIP and self.skip:
            self.skip -= 1
        elif not self.skip and tag == self.block:
            text = re.sub(r"\s+", " ", " ".join(self.buffer)).strip()
            if len(text) >= 35 and text not in self.blocks:
                self.blocks.append(text)
            self.block, self.buffer = None, []

    def handle_data(self, data: str) -> None:
        if not self.skip and self.block:
            self.buffer.append(data)


def fetch(url: str, accept: str) -> bytes:
    request = urllib.request.Request(url, headers={"Accept": accept, "User-Agent": "kiwix-local-search/2.0"})
    with urllib.request.urlopen(request, timeout=10) as response:
        return response.read()


def search(base: str, language: str, subject: str, limit: int) -> list[dict[str, str]]:
    query = urllib.parse.urlencode({"pattern": subject, "books.filter.lang": language, "format": "xml", "pageLength": limit})
    root = ET.fromstring(fetch(f"{base}/search?{query}", "application/xml"))
    results = []
    for item in root.findall(".//item")[:limit]:
        def field(name: str) -> str:
            node = item.find(name)
            return (node.text or "").strip() if node is not None else ""
        url = field("link")
        if url.startswith("/"):
            url = base + url
        results.append({"title": field("title"), "snippet": field("description"), "url": url})
    return results


def score(result: dict[str, str], subject: str) -> float:
    query, title = norm(subject), norm(result["title"])
    query_words, title_words = words(subject), words(result["title"])
    value = 100 if title == query else 0
    value += 40 if title and (title in query or query in title) else 0
    value += 35 * len(query_words & title_words) / len(query_words) if query_words else 0
    value -= 25 if any(word in title for word in ("homonymie", "liste", "bibliographie", "filmographie")) else 0
    return value


def relevant(result: dict[str, str], subject: str) -> bool:
    """Reject unrelated Kiwix fallbacks instead of grounding on a false match."""
    query, title = norm(subject), norm(result["title"])
    query_words, title_words = words(subject), words(result["title"])
    if not query_words or not title_words:
        return False
    if title == query or title in query or query in title:
        return True
    overlap = len(query_words & title_words)
    return overlap >= min(2, len(query_words)) and score(result, subject) >= 30


def fuzzy_pattern(subject: str) -> str:
    """Build one conservative prefix query for a possible minor typo."""
    tokens = norm(subject).split()
    if not tokens or len(tokens) > 5:
        return ""
    shortened = []
    changed = False
    for token in tokens:
        if len(token) >= 6:
            size = max(4, int(len(token) * 0.6))
            shortened.append(token[:size])
            changed |= size < len(token)
        else:
            shortened.append(token)
    return " ".join(shortened) if changed else ""


def fuzzy_score(result: dict[str, str], subject: str) -> float:
    query, title = norm(subject), norm(result["title"])
    if not query or not title:
        return 0.0
    query_tokens, title_tokens = query.split(), title.split()
    token_scores = [
        max((difflib.SequenceMatcher(None, query_token, title_token).ratio() for title_token in title_tokens), default=0.0)
        for query_token in query_tokens
    ]
    coverage = sum(token_scores) / len(token_scores)
    whole = difflib.SequenceMatcher(None, query, title).ratio()
    return 0.7 * coverage + 0.3 * whole


def fuzzy_relevant(result: dict[str, str], subject: str) -> bool:
    """Accept only a near-identical title after the prefix fallback."""
    compact = norm(subject).replace(" ", "")
    return len(compact) >= 5 and fuzzy_score(result, subject) >= 0.82


def article_text(url: str, max_chars: int) -> str:
    parser = TextExtractor()
    parser.feed(fetch(url, "text/html").decode("utf-8", "replace"))
    selected, size = [], 0
    for block in parser.blocks:
        if selected and size + len(block) > max_chars:
            break
        selected.append(block)
        size += len(block) + 2
    return "\n\n".join(selected)[:max_chars]


def emit(payload: dict, code: int = 0) -> int:
    print(json.dumps(payload, ensure_ascii=False))
    return code


def main() -> int:
    cli = argparse.ArgumentParser(description="Search and read one local Kiwix article")
    cli.add_argument("query", help="Canonical subject, e.g. OpenAI")
    cli.add_argument("--search-only", action="store_true")
    cli.add_argument("--limit", type=int, default=int(os.getenv("KIWIX_LIMIT", "6")))
    cli.add_argument("--max-chars", type=int, default=int(os.getenv("KIWIX_MAX_CHARS", "4500")))
    args = cli.parse_args()
    base = os.getenv("KIWIX_URL", "http://localhost:8091").rstrip("/")
    subject = canonical_subject(args.query)
    try:
        results = search(base, os.getenv("KIWIX_LANG", "fra"), subject, max(1, min(args.limit, 10)))
    except Exception as exc:
        return emit({"status": "unreachable", "query": args.query, "detail": str(exc)}, 1)
    ranked = sorted(results, key=lambda result: score(result, subject), reverse=True)
    if args.search_only:
        return emit({"status": "results", "query": args.query, "search_query": subject, "source": base, "results": ranked})

    selected = next((result for result in ranked if relevant(result, subject)), None)
    correction = None
    attempted = [subject]
    if selected is None:
        fallback = fuzzy_pattern(subject)
        if fallback and norm(fallback) != norm(subject):
            attempted.append(fallback)
            try:
                fuzzy_results = search(base, os.getenv("KIWIX_LANG", "fra"), fallback, max(6, min(args.limit, 10)))
            except Exception:
                fuzzy_results = []
            fuzzy_ranked = sorted(fuzzy_results, key=lambda result: fuzzy_score(result, subject), reverse=True)
            if fuzzy_ranked and fuzzy_relevant(fuzzy_ranked[0], subject):
                selected = fuzzy_ranked[0]
                correction = selected["title"]
                ranked = fuzzy_ranked

    if selected is None:
        return emit({
            "status": "no_match",
            "query": args.query,
            "search_query": subject,
            "source": base,
            "results": ranked[:3],
            "attempted": attempted,
            "detail": "No sufficiently relevant article title was found.",
        })
    try:
        text = article_text(selected["url"], max(500, min(args.max_chars, 12000)))
    except Exception as exc:
        return emit({"status": "article_error", "query": args.query, "source": base, "selected": selected, "detail": str(exc)}, 1)
    if not text:
        return emit({"status": "article_empty", "query": args.query, "source": base, "selected": selected}, 1)
    payload = {"status": "ok", "query": args.query, "search_query": correction or subject, "source": base, "selected": selected, "article_text": text, "alternatives": [item for item in ranked if item != selected][:2]}
    if correction:
        payload["correction"] = {"from": subject, "to": correction}
    return emit(payload)


if __name__ == "__main__":
    raise SystemExit(main())

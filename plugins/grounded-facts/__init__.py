"""Hermes plugin: deterministic Kiwix grounding before factual LLM turns."""

from __future__ import annotations

import json
import os
import re
import subprocess
import sys
import threading
import time
from pathlib import Path


DEFAULT_HELPER = str(
    Path(__file__).resolve().parents[2]
    / "skills"
    / "research"
    / "kiwix-local-search"
    / "scripts"
    / "search_kiwix.py"
)

SOCIAL_ONLY = re.compile(
    r"^\s*(salut|bonjour|bonsoir|coucou|hello|hey|merci(?:\s+beaucoup)?|super(?:\s+merci)?|"
    r"ok(?:ay)?|d'accord|parfait|bravo|bien joué|à plus|au revoir)[.!?\s]*$",
    re.IGNORECASE,
)

FACTUAL = re.compile(
    r"(?:\?|\bqui\s+(?:est|était|a\s+créé|a\s+fondé)|\bqu['’]?est[- ]ce\b|"
    r"\bc['’]?est\s+quoi\b|\bquand\b|\boù\b|\bdate\b|\bné[e]?\b|\bmort[e]?\b|"
    r"\bcréateur\b|\bfondateur\b|\bhistoire\b|\bbiograph|\bexplique|\bparle[- ]moi|"
    r"\bcaract[ée]ristiques?\b|\bspecs?\b|\bfiche\s+technique\b|\bprix\b|\bversion\b|"
    r"\bRTX\s*\d+|\bGPU\b|\bCPU\b|\bproduit\b|\blogiciel\b|\bœuvre\b|\bscience\b)",
    re.IGNORECASE,
)

_PROVENANCE_LOCK = threading.Lock()
_PROVENANCE_BY_SESSION = {}


def _store_provenance(session_id: str, payload) -> None:
    """Keep this turn's Kiwix result until Hermes finalizes its response."""
    key = str(session_id or "")
    with _PROVENANCE_LOCK:
        if payload is None:
            _PROVENANCE_BY_SESSION.pop(key, None)
        else:
            _PROVENANCE_BY_SESSION[key] = payload


def _take_provenance(session_id: str):
    """Consume provenance once so it can never leak into a later turn."""
    with _PROVENANCE_LOCK:
        return _PROVENANCE_BY_SESSION.pop(str(session_id or ""), None)


def _markdown_text(value) -> str:
    return str(value or "").replace("\\", "\\\\").replace("[", "\\[").replace("]", "\\]")


def _append_provenance(response_text, session_id="", **kwargs):
    """Deterministically append the Kiwix source after model generation."""
    del kwargs
    provenance = _take_provenance(session_id)
    if not provenance:
        return None

    status = str(provenance.get("status") or "invalid")
    query = _markdown_text(provenance.get("query"))
    if status == "ok":
        title = _markdown_text(provenance.get("title") or "Article Kiwix")
        url = str(provenance.get("url") or "").strip().replace(">", "%3E")
        source = f"[{title}](<{url}>)" if url else title
        footer = (
            "### Provenance\n\n"
            f"- **Source Kiwix :** {source}\n"
            f"- **Preuve d’utilisation :** ✅ `grounded-facts` a injecté automatiquement "
            f"cet article Kiwix dans ce tour (`status=ok`, requête : `{query}`)."
        )
    else:
        detail = _markdown_text(provenance.get("detail"))
        footer = (
            "### Provenance\n\n"
            f"- **Vérification Kiwix :** ⚠️ `grounded-facts` a exécuté la recherche locale "
            f"(`status={_markdown_text(status)}`, requête : `{query}`), mais aucune source Kiwix "
            "n’a été injectée."
        )
        if detail:
            footer += f"\n- **Détail :** {detail}"

    return f"{str(response_text or '').rstrip()}\n\n---\n\n{footer}"


def _message_text(value) -> str:
    if isinstance(value, str):
        return value.strip()
    if isinstance(value, list):
        parts = []
        for item in value:
            if isinstance(item, str):
                parts.append(item)
            elif isinstance(item, dict) and isinstance(item.get("text"), str):
                parts.append(item["text"])
        return "\n".join(parts).strip()
    return str(value or "").strip()


def _needs_grounding(message: str) -> bool:
    if not message or SOCIAL_ONLY.fullmatch(message):
        return False
    return bool(FACTUAL.search(message))


def _ground(user_message, **kwargs):
    session_id = str(kwargs.get("session_id") or "")
    _store_provenance(session_id, None)
    message = _message_text(user_message)
    if not _needs_grounding(message):
        return None

    helper = os.environ.get("KIWIX_HELPER", DEFAULT_HELPER)
    started = time.monotonic()
    try:
        process = subprocess.run(
            [sys.executable, helper, message],
            capture_output=True,
            text=True,
            timeout=20,
            check=False,
        )
        payload = json.loads(process.stdout.strip())
    except Exception as exc:
        payload = {"status": "unreachable", "detail": str(exc)}

    status = payload.get("status", "invalid")
    selected_title = (payload.get("selected") or {}).get("title", "")
    print(
        f"[grounded-facts] pre_llm_call status={status} "
        f"article={selected_title!r} elapsed={time.monotonic() - started:.2f}s",
        file=sys.stderr,
        flush=True,
    )
    selected = payload.get("selected") or {}
    _store_provenance(
        session_id,
        {
            "status": status,
            "query": payload.get("search_query") or payload.get("query") or message,
            "title": selected.get("title", ""),
            "url": selected.get("url", ""),
            "detail": payload.get("detail", ""),
        },
    )
    if status == "ok":
        evidence = payload.get("article_text", "")
        context = (
            "[KIWIX EVIDENCE INJECTED AUTOMATICALLY — do not call Kiwix again]\n"
            f"Sujet recherché : {payload.get('search_query') or payload.get('query')}\n"
            f"Article : {selected.get('title', '')}\n"
            f"URL locale : {selected.get('url', '')}\n"
            f"Texte extrait :\n{evidence}\n\n"
            "RULES FOR THIS ANSWER: use this text only for stable facts. Do not add any name, "
            "number, event, or detail that is absent. If the requested information is missing, "
            "Kiwix is unavailable, or the topic is current, use the Internet and open a primary "
            "official source. A search-result snippet is not a source. Cite only sources actually read."
        )
    else:
        context = (
            "[KIWIX FAILURE INJECTED AUTOMATICALLY — do not call Kiwix again]\n"
            f"Status: {status}. Detail: {payload.get('detail', '')}\n"
            "Before any factual answer, use the Internet and open a primary or institutional source. "
            "Search-result snippets are not sufficient. If no source is accessible, say that the "
            "point is unverified and do not fill the gap from internal knowledge."
        )
    return {"context": context}


def register(ctx):
    ctx.register_hook("pre_llm_call", _ground)
    ctx.register_hook("transform_llm_output", _append_provenance)
    print(
        "[grounded-facts] registered pre_llm_call + transform_llm_output",
        file=sys.stderr,
        flush=True,
    )

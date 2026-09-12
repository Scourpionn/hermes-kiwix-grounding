"""Hermes plugin: deterministic Kiwix grounding before factual LLM turns."""

from __future__ import annotations

import json
import os
import re
import subprocess
import sys
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
    del kwargs
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
    if status == "ok":
        selected = payload.get("selected") or {}
        evidence = payload.get("article_text", "")
        context = (
            "[PREUVE KIWIX INJECTÉE AUTOMATIQUEMENT — ne relance pas Kiwix]\n"
            f"Sujet recherché : {payload.get('search_query') or payload.get('query')}\n"
            f"Article : {selected.get('title', '')}\n"
            f"URL locale : {selected.get('url', '')}\n"
            f"Texte extrait :\n{evidence}\n\n"
            "RÈGLES POUR CETTE RÉPONSE : utilise uniquement ce texte pour les faits stables. "
            "N'ajoute aucun nom, chiffre, événement ou détail absent. Pour un produit, un prix, "
            "une version ou une information actuelle, ouvre en plus la page officielle du fabricant ; "
            "un résultat de moteur de recherche non ouvert n'est pas une source. Cite les sources réellement lues."
        )
    else:
        context = (
            "[ÉCHEC KIWIX INJECTÉ AUTOMATIQUEMENT — ne relance pas Kiwix]\n"
            f"Statut : {status}. Détail : {payload.get('detail', '')}\n"
            "Avant toute réponse factuelle, ouvre une source web primaire ou institutionnelle. "
            "Les extraits d'une page de résultats ne suffisent pas. Si aucune source n'est accessible, "
            "dis que le point n'est pas vérifié et ne complète pas depuis tes connaissances internes."
        )
    return {"context": context}


def register(ctx):
    ctx.register_hook("pre_llm_call", _ground)
    print("[grounded-facts] registered pre_llm_call", file=sys.stderr, flush=True)

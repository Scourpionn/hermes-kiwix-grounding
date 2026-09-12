---
name: kiwix-local-search
description: Mandatory first source for every external factual question, including who, creator, founder, date, place, history, person, organization, product, software, science, culture, or technical specification. Invoke automatically even when the user does not mention Kiwix.
---

# Kiwix local search

Use Kiwix first for stable, checkable knowledge. The helper searches, selects the best result, opens it, and extracts clean text in one call.

## Fast path — mandatory

For an ordinary factual question, run exactly one command:

```bash
python /opt/data/profiles/default/skills/research/kiwix-local-search/scripts/search_kiwix.py "canonical subject"
```

Pass the shortest canonical subject, not the whole question:

- "Qui a fondé OpenAI ?" -> `OpenAI`
- "Qui est Victor Hugo ?" -> `Victor Hugo`
- "Que s'est-il passé à Waterloo ?" -> `Bataille de Waterloo`

The helper also removes common French and English question words and request scaffolding automatically. Therefore, if the model accidentally passes `who created ChatGPT` or `fais une recherche sur Adidas`, the helper searches for the meaningful subject without requiring a second command.

If the exact subject has no relevant result, the helper makes one conservative prefix lookup for minor spelling errors. It accepts a corrected title only when that title is a very close textual match, and reports the change in the `correction` field. Never invent or silently broaden another correction in prose.

The helper also resolves known French Wikipedia title aliases. For example, `Napoleon`, `Napoléon Bonaparte`, and `Bonaparte` are searched as `Napoléon Ier`. Never work around a mismatched result with several manual queries; inspect the single returned status and use the prescribed fallback.

Do not inspect the helper source. Do not use `grep`, inline Python, `curl`, or a browser to parse Kiwix. Do not try several phrasings while `status` is `ok`; `article_text` is the evidence.

## Result

- `status: ok`: answer only from `article_text`; always end with `Source locale : selected.title — selected.url`.
- `status: no_match`, `article_empty`, `article_error`, or `unreachable`: use a current authoritative web source when allowed.
- If the selected title is visibly unrelated, make at most one new call with a clearer canonical title, then use the fallback.

Never fill missing facts from model memory. For changing facts, products, software, prices, availability, laws, or current office holders, use Kiwix first when useful and then verify with an up-to-date primary source.

For a follow-up such as "dis-m'en plus", reuse the retrieved `article_text`. Do not add names, numbers, dates, offers, valuations, records, or technical details absent from that text. If the existing extract cannot support the requested detail, run this same absolute command once for the canonical subject or use the authoritative web fallback.

Greetings, thanks, rewriting, calculations, and analysis of user-provided files do not need Kiwix.

## Configuration

```text
KIWIX_URL=http://localhost:8091
KIWIX_LANG=fra
KIWIX_LIMIT=6
KIWIX_MAX_CHARS=4500
```

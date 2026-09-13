<div align="center">
  <a href="https://kiwix.org/"><img src="https://raw.githubusercontent.com/kiwix/kiwix-android/main/Kiwix_icon_transparent_512x512.png" width="92" alt="Kiwix logo" /></a>
  &nbsp;&nbsp;&nbsp;&nbsp;
  <a href="https://github.com/NousResearch/hermes-agent"><img src="https://raw.githubusercontent.com/NousResearch/hermes-agent/main/assets/banner.png" width="320" alt="Official Hermes Agent logo" /></a>

  # Hermes × Kiwix Grounding

  **Local evidence first. Current verification when it matters.**

  An installable [Hermes](https://github.com/NousResearch/hermes-agent) skill and plugin that ground factual answers in a local Kiwix Server before using the public web.

  [![Release](https://img.shields.io/github/v/release/Scourpionn/hermes-kiwix-grounding?display_name=tag&color=7c3aed)](https://github.com/Scourpionn/hermes-kiwix-grounding/releases/latest)
  [![License](https://img.shields.io/github/license/Scourpionn/hermes-kiwix-grounding?color=22c55e)](LICENSE)
  [![Hermes Agent](https://img.shields.io/badge/Hermes_Agent-v0.21%2B-c8b2fc)](https://github.com/NousResearch/hermes-agent)
  [![Kiwix](https://img.shields.io/badge/Kiwix-local--first-4b8bbe)](https://kiwix.org/)
</div>

---

## Why this exists

Kiwix serves downloaded ZIM archives—such as an offline Wikipedia snapshot—over a local network. That gives Hermes a useful, controllable evidence base when Internet access is unavailable, restricted, costly, or simply not the first source you want to consult.

This project is designed for local knowledge caches on a NAS, offline and field use, classrooms, travel, and privacy-conscious research workflows.

> [!IMPORTANT]
> Kiwix is the first local source, not a replacement for current verification. For news, prices, software releases, availability, laws, regulations, and current office holders, use its context for background and verify the current state on the web.

## How it works

```text
User factual question
        │
        ▼
grounded-facts · pre_llm_call hook
        │
        ▼
Kiwix local search ── usable evidence ──► Inject stable facts into Hermes
        │
        └── no match / unavailable / current topic ──► Open a primary or institutional web source
```

1. The skill derives one short, canonical subject and queries Kiwix once.
2. It selects a relevant local article and returns clean, structured evidence.
3. The `grounded-facts` plugin injects that evidence through `pre_llm_call`; the model does not need to choose a tool.
4. Missing, unavailable, or potentially outdated evidence triggers a web-verification route.
5. A deterministic `transform_llm_output` hook appends the Kiwix source and proof of injection to every grounded answer.
6. The final answer clearly separates local Kiwix evidence, current web verification, and anything unverified.

## Included

| Component | Purpose |
| --- | --- |
| [`skills/kiwix-local-search`](skills/kiwix-local-search) | One-shot lookup helper with French aliases, cautious normalization, and unrelated-result rejection. |
| [`plugins/grounded-facts`](plugins/grounded-facts) | Hermes Agent v0.21+ plugin that registers automatic factual grounding. |
| [`tests`](tests) | Unit tests for canonical subject extraction and relevance safeguards. |

## Install

Copy the two directories into the **target Hermes profile**:

```text
/opt/data/profiles/default/skills/research/kiwix-local-search
/opt/data/profiles/default/plugins/grounded-facts
```

Enable and check the plugin, then restart the Hermes gateway:

```bash
hermes plugins enable grounded-facts
hermes plugins doctor
```

### Configuration

| Variable | Example | Purpose |
| --- | --- | --- |
| `KIWIX_URL` | `http://localhost:8091` | Kiwix Server URL reachable from the Hermes runtime. |
| `KIWIX_LANG` | `fra` | Preferred language / alias. |
| `KIWIX_LIMIT` | `6` | Maximum number of local search results. |
| `KIWIX_MAX_CHARS` | `4500` | Maximum article text returned to Hermes. |

When Kiwix runs on a NAS or another machine, use its LAN or overlay-network address—not `localhost`.

If you use a custom Hermes profile, replace `default` with that profile name.

Detailed references: [skill instructions](skills/kiwix-local-search/SKILL.md) · [plugin instructions](plugins/grounded-facts/README.md) · [Kiwix content catalog](https://get.kiwix.org/en/solutions/catalog/)

## Validate

```bash
python -m unittest discover -s tests -v
```

Then start a new Hermes conversation and ask a factual question without mentioning Kiwix. The plugin should run the local lookup automatically.

## License

MIT — see [LICENSE](LICENSE).

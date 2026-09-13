# Hermes Kiwix Grounding v1.0.1

First GitHub release of the Hermes Kiwix Grounding skill and `grounded-facts` plugin.

## Highlights

- Uses a local Kiwix Server as the first evidence source for factual requests.
- Injects evidence automatically through Hermes' `pre_llm_call` hook, without relying on model tool selection.
- Falls back to an opened primary or institutional web source when local evidence is missing, unavailable, or potentially outdated.
- Keeps the evidence boundary explicit: local Kiwix text supports stable facts only; current facts still require current verification.

## Included

- `skills/kiwix-local-search`: one-shot Kiwix search helper with French aliases, conservative query normalization, and unrelated-result rejection.
- `plugins/grounded-facts`: Hermes Agent v0.21+ plugin that registers the automatic grounding hook.
- Unit tests for canonical subject extraction and unrelated-result rejection.

## Installation

See the repository [README](README.md). Configure `KIWIX_URL` to the Kiwix Server address reachable by the Hermes runtime, enable `grounded-facts`, run `hermes plugins doctor`, then restart the gateway.

## Validation

`python -m unittest discover -s tests -v`

# Hermes Kiwix Grounding

An installable Hermes skill and plugin that use a local Kiwix Server as the first factual source, then fall back to the Internet when local evidence is missing or outdated.

## What is Kiwix?

[Kiwix](https://kiwix.org/en/) is a nonprofit, open-source project that makes knowledge available offline. [Kiwix Server](https://get.kiwix.org/en/solutions/applications/kiwix-server/) serves downloaded ZIM archives—such as an offline Wikipedia snapshot—over a local network, so Hermes can consult a local knowledge base without a live Internet connection.

Typical use cases include a NAS knowledge cache, unreliable or restricted connectivity, classrooms and field work, travel, and emergency/offline operation. The [Kiwix content catalog](https://get.kiwix.org/en/solutions/catalog/) lists available archives, and the [download options](https://get.kiwix.org/en/solutions/applications/download-options/) explain how to install Kiwix Server or a reader.

## How it works

1. The skill normalizes a short canonical subject and queries Kiwix once.
2. It selects a local article and returns its text as structured evidence.
3. The `grounded-facts` plugin injects that evidence through the `pre_llm_call` hook; the model does not need to choose a tool.
4. If Kiwix has no usable evidence, Hermes uses the Internet and opens a current primary or institutional source.
5. The answer distinguishes local Kiwix evidence, current web verification, and anything that remains unverified.

Kiwix is the first local source, not a replacement for current verification. For news, prices, software versions, availability, laws, regulations, and current office holders, use Kiwix for background and verify the current state online.

## Installation

Copy `skills/kiwix-local-search` to `/opt/data/profiles/default/skills/research/` and `plugins/grounded-facts` to `/opt/data/profiles/default/plugins/`. Then enable the plugin with `hermes plugins enable grounded-facts`, run `hermes plugins doctor`, and restart the gateway.

Configure `KIWIX_URL` (for example `http://localhost:8091`), `KIWIX_LANG=fra`, `KIWIX_LIMIT=6`, and `KIWIX_MAX_CHARS=4500`. When Hermes runs on another device, set `KIWIX_URL` to the NAS address reachable from that device.

The plugin is an automatic hook, not a model-selected tool. See the detailed [skill instructions](skills/kiwix-local-search/SKILL.md) and [plugin instructions](plugins/grounded-facts/README.md).

License: MIT. See [LICENSE](LICENSE).

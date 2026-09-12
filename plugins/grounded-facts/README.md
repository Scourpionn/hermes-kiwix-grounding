# grounded-facts for Hermes Agent v0.21+

This plugin automatically runs the Kiwix helper before factual questions and injects the result through `pre_llm_call`. Grounding therefore does not depend on the model choosing a tool by itself.

## What is Kiwix?

[Kiwix](https://kiwix.org/en/) is a nonprofit, open-source project that makes knowledge available offline. A [Kiwix Server](https://get.kiwix.org/en/solutions/applications/kiwix-server/) shares downloaded ZIM archives—such as an offline Wikipedia snapshot—over a local network without requiring live Internet access.

This is useful for:

- research on a NAS or local network;
- unreliable, restricted, or expensive Internet connections;
- classrooms, field work, travel, and emergency/offline situations;
- a fast, reproducible baseline before checking current web sources.

Browse the [Kiwix content catalog](https://get.kiwix.org/en/solutions/catalog/) and [download options](https://get.kiwix.org/en/solutions/applications/download-options/) to install a server or reader and obtain ZIM files.

## Installation in the Hermes runtime

Copy this directory to:

`/opt/data/profiles/default/plugins/grounded-facts`

Then run:

```bash
PLUGIN_DIR="/opt/data/profiles/default/plugins/grounded-facts"
chmod 755 "/opt/data/profiles/default/plugins" "$PLUGIN_DIR"
chmod 644 "$PLUGIN_DIR/plugin.yaml" "$PLUGIN_DIR/__init__.py" "$PLUGIN_DIR/README.md"
hermes plugins enable grounded-facts
hermes plugins doctor
hermes gateway restart
```

Start a new conversation and ask a factual question without mentioning Kiwix. The plugin performs the local lookup automatically.

## Internet fallback

If Kiwix has no matching article, returns an empty or error result, or cannot be reached, the injected guidance tells Hermes to use the Internet and open a current primary or institutional source. Search-result snippets alone are not accepted as evidence. For changing facts, Kiwix provides background and the Internet is used for current verification.

## Optional variables

`KIWIX_HELPER` overrides the helper path. The default is:

`/opt/data/profiles/default/skills/research/kiwix-local-search/scripts/search_kiwix.py`

`KIWIX_URL` points to your Kiwix instance, for example `http://localhost:8091` or a NAS address reachable from Hermes. No API key or private data is required.

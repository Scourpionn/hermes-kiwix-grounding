# grounded-facts pour Hermes Agent v0.21

Ce plugin exécute automatiquement le helper Kiwix avant les questions factuelles et injecte son résultat via `pre_llm_call`. L'appel ne dépend donc plus de la décision du modèle.

## Installation dans le conteneur

Copier ce dossier vers :

`/opt/data/profiles/default/plugins/grounded-facts`

Puis lancer :

```bash
PLUGIN_DIR="/opt/data/profiles/default/plugins/grounded-facts"
chmod 755 "/opt/data/profiles/default/plugins" "$PLUGIN_DIR"
chmod 644 "$PLUGIN_DIR/plugin.yaml" "$PLUGIN_DIR/__init__.py" "$PLUGIN_DIR/README.md"
hermes plugins enable grounded-facts
hermes plugins doctor
hermes gateway restart
```

Commencer ensuite une nouvelle conversation et poser une question factuelle sans mentionner Kiwix.

## Variables facultatives

`KIWIX_HELPER` peut remplacer le chemin du helper. Le chemin par défaut est :

`/opt/data/profiles/default/skills/research/kiwix-local-search/scripts/search_kiwix.py`

Définir `KIWIX_URL` vers votre instance Kiwix, par exemple
`http://localhost:8091`. Aucune clé ni donnée privée n’est requise.

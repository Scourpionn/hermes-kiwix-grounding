# Hermes Kiwix Grounding

Skill et plugin pour utiliser Kiwix comme première source factuelle dans Hermes.

Le skill recherche un sujet canonique, sélectionne un article local et extrait
son texte. Il effectue au plus une correction prudente en cas de faute. Le
plugin `grounded-facts` injecte automatiquement cette preuve via le hook
`pre_llm_call`. En cas d’échec Kiwix, il injecte un état d’échec qui impose une
vérification web primaire séparée.

## Installation

Copier `skills/kiwix-local-search` vers `/opt/data/profiles/<profil>/skills/research/`
et `plugins/grounded-facts` vers `/opt/data/profiles/<profil>/plugins/`.
Activer ensuite le plugin avec `hermes plugins enable grounded-facts`, lancer
`hermes plugins doctor`, puis redémarrer la gateway.

Configurer `KIWIX_URL` (exemple : `http://localhost:8091`), `KIWIX_LANG=fra`,
`KIWIX_LIMIT=6` et `KIWIX_MAX_CHARS=4500`.

Le plugin est un hook invisible, pas un outil choisi par le modèle.

## Sécurité

Aucune clé, adresse NAS personnelle ou donnée utilisateur n’est incluse. Le
fallback web n’est jamais présenté comme une preuve Kiwix. Les informations
actuelles doivent être revérifiées auprès d’une source primaire.

Licence MIT — voir [LICENSE](LICENSE).

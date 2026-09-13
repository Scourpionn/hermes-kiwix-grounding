import importlib.util
from pathlib import Path
import unittest


PROJECT_ROOT = Path(__file__).resolve().parents[1]
PLUGIN_PATH = PROJECT_ROOT / "plugins" / "grounded-facts" / "__init__.py"
spec = importlib.util.spec_from_file_location("grounded_facts_plugin", PLUGIN_PATH)
plugin = importlib.util.module_from_spec(spec)
spec.loader.exec_module(plugin)


class ProvenanceTests(unittest.TestCase):
    def tearDown(self):
        plugin._store_provenance("test-session", None)

    def test_success_appends_source_and_proof_once(self):
        plugin._store_provenance(
            "test-session",
            {
                "status": "ok",
                "query": "Victor Hugo",
                "title": "Victor Hugo",
                "url": "http://kiwix.local/content/wikipedia_fr_all_maxi_2025-05/Victor_Hugo",
            },
        )

        transformed = plugin._append_provenance("Réponse.", session_id="test-session")

        self.assertIn("### Provenance", transformed)
        self.assertIn("**Source Kiwix :**", transformed)
        self.assertIn("Victor Hugo", transformed)
        self.assertIn("**Preuve d’utilisation :**", transformed)
        self.assertIn("`status=ok`", transformed)
        self.assertIsNone(plugin._append_provenance("Tour suivant.", session_id="test-session"))

    def test_failed_lookup_never_claims_source_injection(self):
        plugin._store_provenance(
            "test-session",
            {"status": "unreachable", "query": "Victor Hugo", "detail": "timeout"},
        )

        transformed = plugin._append_provenance("Réponse web.", session_id="test-session")

        self.assertIn("Vérification Kiwix", transformed)
        self.assertIn("aucune source Kiwix n’a été injectée", transformed)
        self.assertNotIn("**Source Kiwix :**", transformed)

    def test_registers_grounding_and_output_transform(self):
        class Context:
            def __init__(self):
                self.hooks = []

            def register_hook(self, name, callback):
                self.hooks.append((name, callback))

        context = Context()
        plugin.register(context)

        self.assertEqual(
            [name for name, _callback in context.hooks],
            ["pre_llm_call", "transform_llm_output"],
        )


if __name__ == "__main__":
    unittest.main()

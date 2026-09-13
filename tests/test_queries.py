import importlib.util
from pathlib import Path
import unittest

PROJECT_ROOT = Path(__file__).resolve().parents[1]
HELPER_PATH = PROJECT_ROOT / 'skills' / 'kiwix-local-search' / 'scripts' / 'search_kiwix.py'

spec = importlib.util.spec_from_file_location('helper', HELPER_PATH)
helper = importlib.util.module_from_spec(spec)
spec.loader.exec_module(helper)


class SubjectTests(unittest.TestCase):
    def test_conversation_request(self):
        for phrase in (
            'oui est ce que tu peux me trouver victor hugo stp ?',
            'Oui, est-ce que tu peux me trouver Victor Hugo stp ?',
            'Peux-tu me trouver Victor Hugo ?',
            'Pouvez-vous nous chercher Victor Hugo svp ?',
        ):
            with self.subTest(phrase=phrase):
                self.assertEqual(helper.norm(helper.canonical_subject(phrase)), 'victor hugo')

    def test_titles_and_existing_aliases(self):
        for subject in ('Victor Hugo', 'Trouver Forrester', 'Oui'):
            self.assertEqual(helper.canonical_subject(subject), subject)
        self.assertEqual(helper.canonical_subject('Napoléon Bonaparte'), 'Napoléon Ier')

    def test_unrelated_result_still_rejected(self):
        self.assertFalse(helper.relevant({'title': 'Louis-Joseph Hugo'}, 'Victor Hugo'))


if __name__ == '__main__':
    unittest.main()

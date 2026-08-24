"""Validate Home Assistant translation catalogues against English."""

import json
from pathlib import Path
import unittest


TRANSLATIONS = (
    Path(__file__).parents[1]
    / "custom_components"
    / "visual_climate_scheduler"
    / "translations"
)
LANGUAGES = {"da", "de", "es", "fi", "fr", "it", "nb", "nl", "sv"}


def _leaf_paths(value, prefix=()):
    if isinstance(value, dict):
        return {
            path
            for key, child in value.items()
            for path in _leaf_paths(child, (*prefix, key))
        }
    return {prefix}


class TranslationTests(unittest.TestCase):
    def test_all_catalogues_are_complete_and_nonempty(self):
        english = json.loads((TRANSLATIONS / "en.json").read_text())
        expected_paths = _leaf_paths(english)

        self.assertEqual(
            LANGUAGES | {"en"},
            {path.stem for path in TRANSLATIONS.glob("*.json")},
        )
        for language in LANGUAGES:
            translated = json.loads((TRANSLATIONS / f"{language}.json").read_text())
            self.assertEqual(expected_paths, _leaf_paths(translated), language)
            for path in expected_paths:
                value = translated
                for key in path:
                    value = value[key]
                self.assertIsInstance(value, str, (language, path))
                self.assertTrue(value.strip(), (language, path))


if __name__ == "__main__":
    unittest.main()

# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

import pathlib
import unittest

import yaml

from odoo_module_migrate import base_migration_script

_RULES_PATH = pathlib.Path(base_migration_script.__file__).parent / "migration_scripts"


class TestYamlRules(unittest.TestCase):
    def test_rule_files_load_identically_with_both_loaders(self):
        """The libyaml loader (when available) and the pure Python loader
        must give the same rules."""
        loader = base_migration_script._YamlLoader
        files = sorted(_RULES_PATH.rglob("*.yaml"))
        self.assertTrue(files)
        for path in files:
            text = path.read_text()
            with self.subTest(path=str(path.relative_to(_RULES_PATH))):
                self.assertEqual(
                    yaml.load(text, Loader=loader),
                    yaml.load(text, Loader=yaml.SafeLoader),
                )

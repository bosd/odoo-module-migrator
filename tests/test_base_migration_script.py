# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

import unittest

from odoo_module_migrate.base_migration_script import BaseMigrationScript
from odoo_module_migrate.migration_scripts import (
    migrate_100_110,
    migrate_150_160,
    migrate_allways,
)


class TestBaseMigrationScript(unittest.TestCase):
    def test_parse_rules_is_idempotent(self):
        script = migrate_150_160.MigrationScript()
        script.parse_rules()
        counts = (
            len(script._RENAMED_FIELDS),
            len(script._RENAMED_MODELS),
            len(script._TEXT_REPLACES.get(".py", {})),
        )
        self.assertTrue(counts[0], "migrate_150_160 should load renamed fields")
        script.parse_rules()
        self.assertEqual(
            counts,
            (
                len(script._RENAMED_FIELDS),
                len(script._RENAMED_MODELS),
                len(script._TEXT_REPLACES.get(".py", {})),
            ),
        )

    def test_rules_do_not_leak_between_scripts(self):
        migrate_150_160.MigrationScript().parse_rules()
        migrate_allways.MigrationScript().parse_rules()

        # Class-level containers must stay untouched
        self.assertEqual(BaseMigrationScript._RENAMED_FIELDS, [])
        self.assertEqual(BaseMigrationScript._RENAMED_MODELS, [])
        self.assertEqual(BaseMigrationScript._TEXT_REPLACES, {})
        self.assertEqual(
            migrate_allways.MigrationScript._GLOBAL_FUNCTIONS,
            [migrate_allways.set_module_installable],
        )
        # A new instance starts from a clean state
        script = migrate_allways.MigrationScript()
        script.parse_rules()
        self.assertEqual(script._RENAMED_FIELDS, [])
        self.assertEqual(len(script._GLOBAL_FUNCTIONS), 2)

    def test_extension_rules_do_not_leak_into_wildcard(self):
        script = migrate_100_110.MigrationScript()
        script.parse_rules()
        wildcard = dict(script._TEXT_REPLACES["*"])
        xml_only = set(script._TEXT_REPLACES[".xml"]) - set(wildcard)
        self.assertTrue(xml_only)

        script._get_patterns(".xml")
        py_replaces = script._get_patterns(".py")[0]

        self.assertEqual(script._TEXT_REPLACES["*"], wildcard)
        py_keys = {pattern.pattern for pattern in py_replaces}
        self.assertFalse(xml_only & py_keys)

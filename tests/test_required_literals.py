# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

import importlib
import pathlib
import pkgutil
import re
import unittest

from odoo_module_migrate import migration_scripts
from odoo_module_migrate.base_migration_script import BaseMigrationScript
from odoo_module_migrate.tools import _could_match, _required_literals

_TESTS_PATH = pathlib.Path(__file__).parent


class TestRequiredLiterals(unittest.TestCase):
    def test_required_literals(self):
        cases = [
            (r"base\.group_configuration", ("base.group_configuration",)),
            # an unescaped dot matches any character
            ("base.group_configuration", ("group_configuration",)),
            # field name is required in every alternative
            (r"""(['"]reference['"]|\.reference[\s,=])""", (".reference", "reference")),
            # optional prefix is ignored
            (r"( |\t)*<openerp>(\n| |\t)*<data>", ("<openerp>",)),
            # alternatives without common literal
            (r"(foo|barbaz)\(", ("barbaz", "foo")),
            # one or more repetitions is required, zero or more is not
            (r"(abc)+x", ("abc",)),
            (r"(abc)*x", ("x",)),
            # case insensitive patterns can not be filtered
            (r"(?i)openerp", None),
            (r"(?i:openerp)x", ("x",)),
            (re.compile("openerp", re.IGNORECASE), None),
            # verbose patterns are parsed with their flags
            (re.compile(r" open erp  # comment", re.VERBOSE), ("openerp",)),
            (r"\s+", None),
            (r"a|\d", None),
        ]
        for pattern, expected in cases:
            with self.subTest(pattern=pattern):
                self.assertEqual(_required_literals(pattern), expected)

    def test_prefilter_never_rejects_a_match(self):
        """For all the rules of all the migration scripts, on all the test
        files: if a pattern matches, its prefilter must accept the text."""
        patterns = set()
        for _loader, name, _is_pkg in pkgutil.iter_modules(migration_scripts.__path__):
            module = importlib.import_module(
                "%s.%s" % (migration_scripts.__name__, name)
            )
            for script_class in vars(module).values():
                if not (
                    isinstance(script_class, type)
                    and issubclass(script_class, BaseMigrationScript)
                    and script_class is not BaseMigrationScript
                ):
                    continue
                script = script_class()
                script.parse_rules()
                for extension in (".py", ".xml", ".js", ".csv", ".txt"):
                    replaces, errors, warnings, _req = script._get_patterns(extension)
                    patterns.update(replaces)
                    patterns.update(p for p, _ in errors + warnings)
        texts = [
            path.read_text()
            for folder in ("data_template", "data_result")
            for path in (_TESTS_PATH / folder).rglob("*")
            if path.is_file() and path.suffix in (".py", ".xml", ".js", ".csv")
        ]
        self.assertTrue(patterns and texts)
        matched = 0
        for pattern in patterns:
            literals = _required_literals(pattern)
            for text in texts:
                if pattern.search(text):
                    matched += 1
                    self.assertTrue(
                        _could_match(literals, text),
                        "Prefilter %r rejects a match of %r" % (literals, pattern),
                    )
        self.assertTrue(matched)

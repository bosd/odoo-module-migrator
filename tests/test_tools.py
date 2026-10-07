# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

import pathlib
import tempfile
import unittest
from unittest import mock

from odoo_module_migrate import tools


class TestRunPreCommit(unittest.TestCase):
    def test_run_pre_commit_on_module_files_only(self):
        with tempfile.TemporaryDirectory() as tmp:
            directory_path = pathlib.Path(tmp)
            (directory_path / "my_module").mkdir()
            (directory_path / "my_module" / "__manifest__.py").write_text("{}")
            (directory_path / "my_module" / "my file.py").write_text("")
            git_files = b"my_module/__manifest__.py\nmy_module/my file.py\n"
            # removed by the migration, but still in the git index
            git_files += b"my_module/migrations/18.0.1.0.0/pre-migration.py\n"

            with mock.patch.object(
                tools, "_execute_shell", return_value=git_files
            ) as execute_shell:
                tools._run_pre_commit(directory_path, ["my_module"])

            ls_files_cmd = execute_shell.call_args_list[0][0][0]
            pre_commit_cmd = execute_shell.call_args_list[1][0][0]
            self.assertIn("git ls-files", ls_files_cmd)
            self.assertIn("-- my_module", ls_files_cmd)
            self.assertEqual(
                pre_commit_cmd,
                "pre-commit run --files my_module/__manifest__.py "
                "'my_module/my file.py'",
            )

    def test_run_pre_commit_without_files(self):
        with mock.patch.object(
            tools, "_execute_shell", return_value=b""
        ) as execute_shell:
            tools._run_pre_commit(pathlib.Path("/tmp"), ["my_module"])
        self.assertEqual(execute_shell.call_count, 1)

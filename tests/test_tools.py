import os
import tempfile
import unittest
from types import SimpleNamespace
from unittest import mock

from tests.helpers import install_fake_dependencies

install_fake_dependencies()

import tools


class ToolsTests(unittest.TestCase):
    def test_read_and_create_file(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            path = os.path.join(tmpdir, "note.txt")
            result = tools.create_file.invoke({"path": path, "content": "hello"})
            self.assertEqual(result, f"Created {path}")
            self.assertEqual(tools.read_file.invoke({"path": path}), "hello")

    def test_create_file_rejects_existing_file(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            path = os.path.join(tmpdir, "note.txt")
            with open(path, "w") as f:
                f.write("existing")
            result = tools.create_file.invoke({"path": path, "content": "new"})
            self.assertIn("already exists", result)

    def test_fuzzy_match_and_apply_edit_support_whitespace_insensitive_match(self):
        self.assertTrue(tools._fuzzy_match(" a\n b ", "a\nb"))
        updated = tools._apply_edit("start\n  old value\nend\n", "old value", "new value")
        self.assertEqual(updated, "start\n  new value\nend\n")

    def test_apply_edit_raises_when_text_not_found(self):
        with self.assertRaises(ValueError):
            tools._apply_edit("hello", "missing", "world")

    def test_edit_file_applies_multiple_edits(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            path = os.path.join(tmpdir, "file.txt")
            with open(path, "w") as f:
                f.write("alpha\nbeta\n")
            result = tools.edit_file.invoke(
                {
                    "path": path,
                    "edits": [
                        {"old_text": "alpha", "new_text": "one"},
                        {"old_text": "beta", "new_text": "two"},
                    ],
                }
            )
            self.assertEqual(result, f"Applied 2 edit(s) to {path}")
            with open(path, "r") as f:
                self.assertEqual(f.read(), "one\ntwo\n")

    def test_run_command_returns_combined_output(self):
        completed = SimpleNamespace(stdout="out\n", stderr="err\n")
        with mock.patch("tools.subprocess.run", return_value=completed) as run_mock:
            result = tools.run_command.invoke({"command": "echo hi"})
        run_mock.assert_called_once()
        self.assertEqual(result, "out\nerr")

    def test_list_files_prefers_git_output(self):
        completed = SimpleNamespace(returncode=0, stdout="a.py\nb.py\n")
        with mock.patch("tools.subprocess.run", return_value=completed):
            result = tools.list_files.invoke({"path": "."})
        self.assertEqual(result, "a.py\nb.py")

    def test_list_files_falls_back_to_os_walk(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            os.makedirs(os.path.join(tmpdir, "pkg"), exist_ok=True)
            os.makedirs(os.path.join(tmpdir, ".hidden"), exist_ok=True)
            os.makedirs(os.path.join(tmpdir, "__pycache__"), exist_ok=True)
            with open(os.path.join(tmpdir, "pkg", "main.py"), "w") as f:
                f.write("print('hi')")
            with open(os.path.join(tmpdir, ".hidden", "secret.txt"), "w") as f:
                f.write("secret")

            with mock.patch("tools.subprocess.run", side_effect=FileNotFoundError):
                result = tools.list_files.invoke({"path": tmpdir})

            self.assertIn(os.path.join(tmpdir, "pkg", "main.py"), result)
            self.assertNotIn("secret.txt", result)

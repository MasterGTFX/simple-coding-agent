import json
import os
import tempfile
import unittest

import config


class ConfigTests(unittest.TestCase):
    def test_load_config_returns_empty_when_missing(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            old_cwd = os.getcwd()
            os.chdir(tmpdir)
            try:
                self.assertEqual(config.load_config(), {})
            finally:
                os.chdir(old_cwd)

    def test_load_config_returns_empty_for_invalid_json(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            old_cwd = os.getcwd()
            os.chdir(tmpdir)
            try:
                os.makedirs(config.CONFIG_DIR, exist_ok=True)
                with open(config.CONFIG_FILE, "w") as f:
                    f.write("not json")
                self.assertEqual(config.load_config(), {})
            finally:
                os.chdir(old_cwd)

    def test_save_config_persists_key_value(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            old_cwd = os.getcwd()
            os.chdir(tmpdir)
            try:
                config.save_config("model", "openai/gpt-test")
                with open(config.CONFIG_FILE, "r") as f:
                    data = json.load(f)
                self.assertEqual(data, {"model": "openai/gpt-test"})
                self.assertEqual(config.load_config(), data)
            finally:
                os.chdir(old_cwd)

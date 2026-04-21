import json
import os
import tempfile
import unittest
from unittest import mock

import config


class ConfigTests(unittest.TestCase):
    def test_load_config_returns_empty_when_missing(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            with mock.patch.dict(os.environ, {"AGENT_CONFIG_DIR": tmpdir}):
                self.assertEqual(config.load_config(), {})

    def test_load_config_returns_empty_for_invalid_json(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            with mock.patch.dict(os.environ, {"AGENT_CONFIG_DIR": tmpdir}):
                os.makedirs(config.get_config_dir(), exist_ok=True)
                with open(config.get_config_file(), "w") as f:
                    f.write("not json")
                self.assertEqual(config.load_config(), {})

    def test_save_config_persists_key_value(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            with mock.patch.dict(os.environ, {"AGENT_CONFIG_DIR": tmpdir}):
                config.save_config("model", "openai/gpt-test")
                with open(config.get_config_file(), "r") as f:
                    data = json.load(f)
                self.assertEqual(data, {"model": "openai/gpt-test"})
                self.assertEqual(config.load_config(), data)

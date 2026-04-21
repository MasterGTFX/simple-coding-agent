import json
import os
import sys
import tempfile
import types
import unittest
from unittest import mock

from tests.helpers import SystemMessage, install_fake_dependencies

install_fake_dependencies()

import commands


class CommandsTests(unittest.TestCase):
    def test_cmd_new_resets_messages_to_system_only(self):
        state = {"messages": [SystemMessage(content="sys"), "extra"], "session_id": "old"}
        self.assertTrue(commands.cmd_new(state))
        self.assertEqual(len(state["messages"]), 1)
        self.assertEqual(state["messages"][0].content, "sys")
        self.assertNotEqual(state["session_id"], "old")

    def test_fetch_models_openai_filters_expected_ids(self):
        fake_openai = types.ModuleType("openai")

        class OpenAI:
            def __init__(self):
                data = [
                    types.SimpleNamespace(id="gpt-4o"),
                    types.SimpleNamespace(id="o3-mini"),
                    types.SimpleNamespace(id="text-embedding-3-small"),
                ]
                self.models = types.SimpleNamespace(list=lambda: types.SimpleNamespace(data=data))

        fake_openai.OpenAI = OpenAI

        with mock.patch.dict(sys.modules, {"openai": fake_openai}):
            models = commands.fetch_models("openai")

        self.assertEqual(models[:-1], ["o3-mini", "gpt-4o"])
        self.assertEqual(models[-1], "custom...")

    def test_fetch_models_handles_errors(self):
        with mock.patch.dict(sys.modules, {"openai": None}):
            with mock.patch("builtins.print") as print_mock:
                models = commands.fetch_models("openai")
        self.assertEqual(models, ["custom..."])
        print_mock.assert_called()

    def test_cmd_model_sets_state_and_saves_config(self):
        state = {"model": None, "llm": None}
        fake_bound = object()
        fake_llm = mock.Mock()
        fake_llm.bind_tools.return_value = fake_bound

        with mock.patch("llm.create_llm", return_value=fake_llm) as create_llm_mock, \
             mock.patch("config.save_config") as save_config_mock:
            self.assertTrue(commands.cmd_model(state, "openai/gpt-test"))

        create_llm_mock.assert_called_once_with("openai/gpt-test")
        save_config_mock.assert_called_once_with("model", "openai/gpt-test")
        self.assertEqual(state["model"], "openai/gpt-test")
        self.assertIs(state["llm"], fake_bound)

    def test_cmd_model_does_not_mutate_state_when_creation_fails(self):
        state = {"model": "old", "llm": "old-llm"}
        with mock.patch("llm.create_llm", side_effect=RuntimeError("boom")):
            self.assertTrue(commands.cmd_model(state, "openai/new"))
        self.assertEqual(state["model"], "old")
        self.assertEqual(state["llm"], "old-llm")

    def test_cmd_model_interactive_cancel(self):
        state = {"model": None, "llm": None}
        with mock.patch("builtins.input", return_value=""):
            self.assertTrue(commands.cmd_model(state))
        self.assertIsNone(state["model"])

    def test_cmd_system_and_help_print_output(self):
        state = {"messages": [SystemMessage(content="system prompt")]}
        with mock.patch("builtins.print") as print_mock:
            self.assertTrue(commands.cmd_system(state))
            self.assertTrue(commands.cmd_help(state))
        printed = "\n".join(" ".join(map(str, call.args)) for call in print_mock.call_args_list)
        self.assertIn("system prompt", printed)
        self.assertIn("/new", printed)
        self.assertIn("/model", printed)

    def test_cmd_exit_raises_system_exit(self):
        with self.assertRaises(SystemExit):
            commands.cmd_exit({})

    def test_cmd_fork_changes_session_id(self):
        state = {"session_id": "old"}
        self.assertTrue(commands.cmd_fork(state))
        self.assertNotEqual(state["session_id"], "old")

    def test_cmd_resume_handles_missing_directory(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            old_cwd = os.getcwd()
            os.chdir(tmpdir)
            try:
                with mock.patch("builtins.print") as print_mock:
                    self.assertTrue(commands.cmd_resume({"messages": []}))
                self.assertIn("No sessions found.", print_mock.call_args_list[0].args[0])
            finally:
                os.chdir(old_cwd)

    def test_cmd_resume_loads_specific_session(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            old_cwd = os.getcwd()
            os.chdir(tmpdir)
            try:
                os.makedirs(".coding-agent", exist_ok=True)
                session_path = os.path.join(".coding-agent", "session1.json")
                with open(session_path, "w") as f:
                    json.dump([{"type": "system", "data": {"content": "hello"}}], f)

                state = {"messages": [], "session_id": "old"}
                fake_messages = [SystemMessage(content="restored")]
                with mock.patch("commands.messages_from_dict", return_value=fake_messages):
                    self.assertTrue(commands.cmd_resume(state, "session1"))

                self.assertEqual(state["messages"], fake_messages)
                self.assertEqual(state["session_id"], "session1")
            finally:
                os.chdir(old_cwd)

    def test_handle_routes_known_and_unknown_commands(self):
        state = {"messages": [SystemMessage(content="sys")], "session_id": "1", "model": None, "llm": None}
        self.assertFalse(commands.handle("hello", state))

        with mock.patch.object(commands, "cmd_new", return_value=True) as new_mock:
            commands.COMMANDS["new"] = commands.cmd_new
            self.assertTrue(commands.handle("/new", state))
            new_mock.assert_called_once_with(state)

        with mock.patch("builtins.print") as print_mock:
            self.assertTrue(commands.handle("/does-not-exist", state))
        self.assertIn("Unknown command", print_mock.call_args.args[0])

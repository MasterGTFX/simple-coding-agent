import importlib
import os
import sys
import tempfile
import unittest
from types import SimpleNamespace
from unittest import mock

from tests.helpers import install_fake_dependencies

install_fake_dependencies()


class AgentTests(unittest.TestCase):
    def import_agent_fresh(self, cwd):
        old_cwd = os.getcwd()
        try:
            os.chdir(cwd)
            sys.modules.pop("agent", None)
            with mock.patch("config.load_config", return_value={}), \
                 mock.patch.dict(os.environ, {"AGENT_MODEL": ""}, clear=False):
                return importlib.import_module("agent")
        finally:
            os.chdir(old_cwd)

    def test_save_session_writes_session_json(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            agent = self.import_agent_fresh(tmpdir)
            old_cwd = os.getcwd()
            try:
                os.chdir(tmpdir)
                agent.save_session()
            finally:
                os.chdir(old_cwd)
            path = os.path.join(tmpdir, ".coding-agent", f"{agent.state['session_id']}.json")
            self.assertTrue(os.path.exists(path))

    def test_invoke_with_spinner_returns_llm_result(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            agent = self.import_agent_fresh(tmpdir)
            llm = mock.Mock()
            llm.invoke.return_value = "done"
            with mock.patch("agent.time.sleep", return_value=None):
                self.assertEqual(agent.invoke_with_spinner(llm, ["msg"]), "done")
            llm.invoke.assert_called_once_with(["msg"])

    def test_invoke_with_spinner_raises_llm_exception(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            agent = self.import_agent_fresh(tmpdir)
            llm = mock.Mock()
            llm.invoke.side_effect = RuntimeError("boom")
            with mock.patch("agent.time.sleep", return_value=None):
                with self.assertRaises(RuntimeError):
                    agent.invoke_with_spinner(llm, ["msg"])

    def test_print_ai_message_handles_reasoning_and_text_blocks(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            agent = self.import_agent_fresh(tmpdir)
            msg = SimpleNamespace(
                additional_kwargs={},
                response_metadata={"provider_extra": {"reasoning": "because"}},
                content=[
                    {"type": "thinking", "thinking": "step one"},
                    {"type": "text", "text": "final answer"},
                ],
            )
            with mock.patch("builtins.print") as print_mock:
                agent.print_ai_message(msg)
            printed = "\n".join(" ".join(map(str, call.args)) for call in print_mock.call_args_list)
            self.assertIn("because", printed)
            self.assertIn("step one", printed)
            self.assertIn("final answer", printed)

    def test_run_handles_slash_command_without_calling_llm(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            agent = self.import_agent_fresh(tmpdir)
            agent.state["llm"] = mock.Mock()
            with mock.patch("agent.handle", return_value=True) as handle_mock, \
                 mock.patch("agent.save_session") as save_mock:
                agent.run("/help")
            handle_mock.assert_called_once_with("/help", agent.state)
            save_mock.assert_called_once()
            agent.state["llm"].invoke.assert_not_called()

    def test_run_executes_tool_calls_and_prints_final_response(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            agent = self.import_agent_fresh(tmpdir)

            tool = mock.Mock()
            tool.name = "read_file"
            tool.invoke.return_value = "tool result"
            agent.tools_map = {"read_file": tool}

            first = SimpleNamespace(tool_calls=[{"name": "read_file", "args": {"path": "x"}, "id": "call-1"}])
            second = SimpleNamespace(tool_calls=[], content="all done")
            agent.state["llm"] = mock.Mock()
            agent.state["llm"].invoke.side_effect = [first, second]

            with mock.patch("agent.handle", return_value=False), \
                 mock.patch("agent.save_session"), \
                 mock.patch("agent.print_ai_message") as print_ai_mock, \
                 mock.patch("agent.invoke_with_spinner", side_effect=[first, second]):
                agent.run("read something")

            tool.invoke.assert_called_once_with({"path": "x"})
            print_ai_mock.assert_called_once_with(second)
            self.assertEqual(agent.state["messages"][-2].content, "tool result")
            self.assertEqual(agent.state["messages"][-1].content, "all done")

    def test_main_prompts_for_model_then_runs_cli_input(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            agent = self.import_agent_fresh(tmpdir)
            agent.state["model"] = None
            agent.state["llm"] = None

            def set_model(state):
                state["model"] = "openai/gpt-test"

            with mock.patch("commands.cmd_model", side_effect=set_model) as cmd_model_mock, \
                 mock.patch.object(sys, "argv", ["agent.py", "do work"]), \
                 mock.patch("agent.run") as run_mock:
                agent.main()

            cmd_model_mock.assert_called_once_with(agent.state)
            run_mock.assert_called_once_with("do work")

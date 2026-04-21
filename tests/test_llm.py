import os
import sys
import types
import unittest
from unittest import mock

from tests.helpers import install_fake_dependencies

install_fake_dependencies()

import llm


class LlmTests(unittest.TestCase):
    def test_create_llm_uses_anthropic_for_explicit_provider(self):
        fake_module = types.ModuleType("langchain_anthropic")

        class FakeChatAnthropic:
            def __init__(self, **kwargs):
                self.kwargs = kwargs

        fake_module.ChatAnthropic = FakeChatAnthropic

        with mock.patch.dict(sys.modules, {"langchain_anthropic": fake_module}):
            model = llm.create_llm("anthropic/claude-test", temperature=0.2)

        self.assertIsInstance(model, FakeChatAnthropic)
        self.assertEqual(model.kwargs["model"], "claude-test")
        self.assertEqual(model.kwargs["temperature"], 0.2)

    def test_create_llm_detects_google_from_model_name(self):
        fake_module = types.ModuleType("langchain_google_genai")

        class FakeGoogleModel:
            def __init__(self, **kwargs):
                self.kwargs = kwargs

        fake_module.ChatGoogleGenerativeAI = FakeGoogleModel

        with mock.patch.dict(sys.modules, {"langchain_google_genai": fake_module}):
            model = llm.create_llm("gemini-2.0-flash")

        self.assertIsInstance(model, FakeGoogleModel)
        self.assertEqual(model.kwargs["model"], "gemini-2.0-flash")

    def test_create_llm_configures_openrouter(self):
        fake_module = types.ModuleType("langchain_openai")

        class FakeChatOpenAI:
            def __init__(self, **kwargs):
                self.kwargs = kwargs

        fake_module.ChatOpenAI = FakeChatOpenAI

        with mock.patch.dict(sys.modules, {"langchain_openai": fake_module}):
            with mock.patch.dict(os.environ, {"OPENROUTER_API_KEY": "router-key"}, clear=False):
                model = llm.create_llm("openrouter/anthropic/claude-3-opus", temperature=0.1)

        self.assertIsInstance(model, FakeChatOpenAI)
        self.assertEqual(model.kwargs["model"], "anthropic/claude-3-opus")
        self.assertEqual(model.kwargs["api_key"], "router-key")
        self.assertEqual(model.kwargs["base_url"], "https://openrouter.ai/api/v1")
        self.assertEqual(model.kwargs["extra_body"], {"include_reasoning": True})
        self.assertEqual(model.kwargs["temperature"], 0.1)

    def test_create_llm_configures_ollama(self):
        fake_module = types.ModuleType("langchain_openai")

        class FakeChatOpenAI:
            def __init__(self, **kwargs):
                self.kwargs = kwargs

        fake_module.ChatOpenAI = FakeChatOpenAI

        with mock.patch.dict(sys.modules, {"langchain_openai": fake_module}):
            with mock.patch.dict(os.environ, {"OLLAMA_BASE_URL": "http://ollama:11434/v1"}, clear=False):
                model = llm.create_llm("ollama/codellama")

        self.assertEqual(model.kwargs["model"], "codellama")
        self.assertEqual(model.kwargs["api_key"], "ollama")
        self.assertEqual(model.kwargs["base_url"], "http://ollama:11434/v1")

    def test_create_llm_defaults_to_openai(self):
        fake_module = types.ModuleType("langchain_openai")

        class FakeChatOpenAI:
            def __init__(self, **kwargs):
                self.kwargs = kwargs

        fake_module.ChatOpenAI = FakeChatOpenAI

        with mock.patch.dict(sys.modules, {"langchain_openai": fake_module}):
            model = llm.create_llm("gpt-4o-mini")

        self.assertIsInstance(model, FakeChatOpenAI)
        self.assertEqual(model.kwargs, {"model": "gpt-4o-mini"})

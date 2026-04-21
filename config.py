import json
import os
import sys
from typing import Any

APP_NAME = "simple-coding-agent"


def get_config_dir() -> str:
    override = os.environ.get("AGENT_CONFIG_DIR")
    if override:
        return override

    try:
        from platformdirs import user_config_dir

        return user_config_dir(APP_NAME, APP_NAME)
    except ImportError:
        if sys.platform == "win32":
            base = os.environ.get("APPDATA") or os.environ.get("LOCALAPPDATA") or os.path.expanduser("~")
            return os.path.join(base, APP_NAME)
        if sys.platform == "darwin":
            return os.path.join(os.path.expanduser("~/Library/Application Support"), APP_NAME)
        base = os.environ.get("XDG_CONFIG_HOME", os.path.expanduser("~/.config"))
        return os.path.join(base, APP_NAME)


def get_config_file() -> str:
    return os.path.join(get_config_dir(), "config.json")


def load_config() -> dict:
    config_file = get_config_file()
    if os.path.exists(config_file):
        try:
            with open(config_file, "r") as f:
                return json.load(f)
        except Exception:
            pass
    return {}


def save_config(key: str, value: Any):
    config_dir = get_config_dir()
    config_file = get_config_file()
    os.makedirs(config_dir, exist_ok=True)
    config = load_config()
    config[key] = value
    with open(config_file, "w") as f:
        json.dump(config, f, indent=2)

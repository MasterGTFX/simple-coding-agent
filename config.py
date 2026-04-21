import os
import json
from typing import Any

CONFIG_DIR = ".coding-agent"
CONFIG_FILE = os.path.join(CONFIG_DIR, "config.json")

def load_config() -> dict:
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, "r") as f:
                return json.load(f)
        except Exception:
            pass
    return {}

def save_config(key: str, value: Any):
    os.makedirs(CONFIG_DIR, exist_ok=True)
    config = load_config()
    config[key] = value
    with open(CONFIG_FILE, "w") as f:
        json.dump(config, f, indent=2)

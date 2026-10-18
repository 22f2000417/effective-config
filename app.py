import os
from pathlib import Path

import yaml
from dotenv import dotenv_values
from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

DEFAULTS = {
    "port": 8000,
    "workers": 1,
    "debug": False,
    "log_level": "info",
    "api_key": "default-secret-000",
}

BASE_DIR = Path(__file__).parent
CONFIG_FILE = BASE_DIR / "config.development.yaml"
ENV_FILE = BASE_DIR / ".env"


def normalize_env(values):
    result = {}
    for key, value in values.items():
        if value is None:
            continue
        if key == "NUM_WORKERS":
            result["workers"] = value
        elif key.startswith("APP_"):
            result[key[4:].lower()] = value
    return result


def coerce(key, value):
    if key in ("port", "workers"):
        return int(value)
    if key == "debug":
        if isinstance(value, bool):
            return value
        return str(value).strip().lower() in (
            "true", "1", "yes", "on"
        )
    return str(value)


@app.get("/effective-config")
def effective_config(set: list[str] = Query(default=[])):
    config = DEFAULTS.copy()

    if CONFIG_FILE.exists():
        with open(CONFIG_FILE, encoding="utf-8") as f:
            config.update(yaml.safe_load(f) or {})

    config.update(normalize_env(dotenv_values(ENV_FILE)))
    config.update(normalize_env(os.environ))

    for item in set:
        if "=" not in item:
            continue
        key, value = item.split("=", 1)
        key = key.strip().lower()
        if key:
            config[key] = value

    config = {
        key: coerce(key, value)
        for key, value in config.items()
    }

    if "api_key" in config:
        config["api_key"] = "****"

    return config

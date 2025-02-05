# src/settings.py
from pathlib import Path
import yaml
import os
from typing import Dict, Any


class Settings:
    def __init__(self, config_path: Path):
        self.config = self._load_config(config_path)

    def _load_config(self, path: Path) -> Dict[str, Any]:
        with open(path) as f:
            config = yaml.safe_load(f)

        # Replace environment variables in config
        self._replace_env_vars(config)
        return config

    def _replace_env_vars(self, config: Dict[str, Any]) -> None:
        """Recursively replace environment variable placeholders in config"""
        for key, value in config.items():
            if isinstance(value, dict):
                self._replace_env_vars(value)
            elif isinstance(value, str) and value.startswith("${") and value.endswith("}"):
                env_var = value[2:-1]
                config[key] = os.getenv(env_var)
                if config[key] is None:
                    raise ValueError(f"Required environment variable {env_var} is not set")

    @property
    def together_api_key(self) -> str:
        api_key = self.config['llm']['together_api_key']
        if not api_key:
            raise ValueError("Together API key not found in environment variables")
        return api_key

    @property
    def db_path(self) -> Path:
        return Path(self.config['storage']['db_path'])
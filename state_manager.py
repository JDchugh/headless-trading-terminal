import json
import os

class StateManager:
    def __init__(self, filepath="state.json"):
        self.filepath = filepath
        self.cache = self._load_all()

    def save_state(self, strategy_name: str, state_dict: dict):
        self.cache[strategy_name] = state_dict
        with open(self.filepath, "w") as f:
            json.dump(self.cache, f, indent=4)

    def load_state(self, strategy_name: str) -> dict:
        return self.cache.get(strategy_name, {})

    def _load_all(self) -> dict:
        if not os.path.exists(self.filepath):
            return {}
        try:
            with open(self.filepath, "r") as f:
                return json.load(f)
        except json.JSONDecodeError:
            return {}

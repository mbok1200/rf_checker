import diskcache as dc
import hashlib
import json


class State(object):
     machine: str = "default"
     game_name: str = ""
     metadata: dict = {}
     urls: list[str] = []
     def __init__(self):
        self.cache = dc.Cache(".ai_core_state_cache")
     def make_key(self, prompt: str):
          return hashlib.sha256(prompt.encode()).hexdigest()
     def set(self, key: str, value):
        setattr(self, key, value)
     def insert_metadata(self, key: str, value):
        self.metadata[key] = value
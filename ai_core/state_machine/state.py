class State(object):
   machine: str = "default"
   metadata: dict = {}
   def __setattr__(self, name, value):
        if name == "machine" or not isinstance(value, str):
           raise ValueError("machine must be a string")
        super().__setattr__(name, value)
   def insert_metadata(self, key: str, value):
        self.metadata[key] = value
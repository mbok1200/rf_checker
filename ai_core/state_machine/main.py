from .state import State
from .config import Config

class StateMachine(object):
    def __init__(self):
        self.state = State()
        self.config = Config()
    def setState(self, state: State):
        self.state = state
from state_machine.state import State
from state_machine.config import Config

class StateMachine(object):
    def __init__(self):
        self.state = State()
        self.config = Config()
    def setState(self, state: State):
        self.state = State(state)
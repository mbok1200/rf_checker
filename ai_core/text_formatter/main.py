from .Detector import *
from ..state_machine.main import *

class TextFormatterMain: 
    def __init__(self):
        self.state_machine = StateMachine()
        self.state = self.state_machine.state
    def run(self):
        text = self.state.metadata.get("text", "")
        detector = Detector(text)
        self.state.insert_metadata("text_detected",  detector.detect_language())
from text_formatter.Detector import *
from state_machine.main import *

class TextFormatterMain: 
    def __init__(self):
        self.state_machine = StateMachine()
    def run(self):
        text = self.state_machine.metadata.get("text", "")
        detector = Detector(text)
        print("Detected language:", detector.detect_language())
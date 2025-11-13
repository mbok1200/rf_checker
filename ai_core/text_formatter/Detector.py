from langdetect import detect

class Detector:

    def __init__(self, text: str):
        self.text = text

    def detect_language(self) -> str:
        return detect(self.text)
from .urls_checker import UrlsChecker
from ..state_machine.main import StateMachine
class RequestHandler:
    def __init__(self):
        self.state_machine =StateMachine()
        self.state = self.state_machine.state
        self.config = self.state_machine.config
    def handle_urls(self):
        urls = self.state.metadata.get("urls", [])
        print(f"Handling URLs: {urls}")
        checker = UrlsChecker(urls)
        results = checker.run()
        return results

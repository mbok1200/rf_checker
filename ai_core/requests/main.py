from requests.urls_checker import UrlsChecker
from ai_core.state_machine.main import StateMachine
class RequestHandler:
    def __init__(self):
        self.state_machine = StateMachine()
    def handle_urls(self):
        urls = self.state_machine.config.get("urls", [])
        checker = UrlsChecker(urls)
        results = checker.run()
        return results

from .text_formatter.main import TextFormatterMain
from .requests_methods.main import RequestHandler
from .state_machine.main import StateMachine
from .requests_methods.steam.main import SteamMain
from .ai_machines.main import AIMachinesMain
from dotenv import load_dotenv
import pathlib
# Завантаження .env з кореня проєкту (rf_checker/.env)
ROOT_DIR = pathlib.Path(__file__).resolve().parent.parent
load_dotenv(dotenv_path=ROOT_DIR / ".env")

class AICoreMain: 
    def __init__(self):
        self.ai_machines = AIMachinesMain()
        self.state_machine = StateMachine()
        self.state = self.state_machine.state
        self.config = self.state_machine.config
        self.text_formatter = TextFormatterMain()
        self.request_handler = RequestHandler()
    def text_format(self):
        self.text_formatter.run()
    def request_handle(self, urls: list[str] = []):
        self.state.insert_metadata("urls", urls)
        meta = self.request_handler.handle_urls()
        self.state.insert_metadata("urls_metadata", meta)
    def steam_process(self, game_name: str = "Half-Life 2"):
        steam = SteamMain()
        self.state.insert_metadata("game_name", game_name)
        self.state.insert_metadata("steam_game_info", steam.get_steam_game_info_by_name(game_name))
    def run(self):
        # valid steam processing
        self.steam_process("Hades")
        response = self.ai_machines.gemeni_generate_text(self.state.metadata)
        self.state.insert_metadata("response", response)
        
        print(f"After Text Formatting:, {self.state.metadata.get('response')}")
        pass
        

if __name__ == "__main__":
    main = AICoreMain()
    main.run()
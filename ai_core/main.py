from text_formatter.main import *
from requests.main import *
from state_machine.main import *
from requests.steam.main import *

class AICoreMain: 
    def __init__(self):
        self.state_machine = StateMachine()
    def run(self):
        # valid text processing
        text = TextFormatterMain()
        text.run()
        # valid requests processing
        meta = RequestHandler().handle_urls()
        self.state_machine.state.insert_metadata("urls_metadata", meta)
        # valid steam processing
        steam = SteamMain()
        self.state_machine.state.insert_metadata("steam_game_info", steam.get_steam_game_info_by_name("Half-Life 2"))

if __name__ == "__main__":
    main = AICoreMain()
    main.run()
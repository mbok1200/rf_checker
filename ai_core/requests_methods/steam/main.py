import requests

class SteamMain:
    def __init__(self):
        pass
    def search_steam_app_id(self, game_name: str) -> int | None:
        """
        Шукає гру в Steam і повертає її app_id за назвою.
        """
        url = f"https://steamcommunity.com/actions/SearchApps/{game_name}"
        resp = requests.get(url)
        results = resp.json()

        if not results:
            return None
        return results[0]["appid"]  # беремо першу гру з результатів
    def get_steam_game_info_by_name(self, game_name: str) -> dict:
        """
        Шукає гру за назвою і повертає всі метадані з Steam.
        """
        app_id = self.search_steam_app_id(game_name)
        if not app_id:
            return {"error": f"Game '{game_name}' not found"}

        url = f"https://store.steampowered.com/api/appdetails?appids={app_id}&cc=us&l=en"
        resp = requests.get(url)
        data = resp.json()

        if not data[str(app_id)]["success"]:
            return {"error": f"Game data not available for '{game_name}'"}

        game_data = data[str(app_id)]["data"]

        info = {
            "app_id": app_id,
            "name": game_data.get("name"),
            "type": game_data.get("type"),
            "developers": game_data.get("developers"),
            "publishers": game_data.get("publishers"),
            "release_date": game_data.get("release_date", {}).get("date"),
            "price": game_data.get("price_overview", {}).get("final_formatted"),
            "genres": [g["description"] for g in game_data.get("genres", [])],
            "categories": [c["description"] for c in game_data.get("categories", [])],
            "metacritic_score": game_data.get("metacritic", {}).get("score"),
            "header_image": game_data.get("header_image"),
            "background": game_data.get("background_raw"),
            "website": game_data.get("website"),
            "short_description": game_data.get("short_description"),
            "supported_languages": game_data.get("supported_languages"),
        }

        return info
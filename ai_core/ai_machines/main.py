from .gemini import GeminiAI
from .openai import OpenAIMachine
import json, pathlib

class AIMachinesMain:
    def __init__(self):
        self.gemini_ai = GeminiAI()  # Initialize GeminiAI instance later
        self.openai_ai = OpenAIMachine()  # Initialize OpenAI instance here
        self.prompt_data = self._load_prompts()
    def _load_prompts(self) -> dict:
        """Безпечне завантаження validation.json з кількох можливих місць."""
        base_dir = pathlib.Path(__file__).resolve().parent  # ai_machines/
        candidates = [
            base_dir / "prompts" / "validation.json",                   # ai_core/ai_machines/prompts/validation.json
            base_dir.parent / "prompts" / "validation.json",            # ai_core/prompts/validation.json
            base_dir.parent.parent / "prompts" / "validation.json"      # проект/prompts/validation.json
        ]
        for p in candidates:
            if p.exists():
                try:
                    with open(p, "r", encoding="utf-8") as f:
                        return json.load(f)
                except Exception:
                    break
        # Fallback якщо файл відсутній або зламаний
        return {
            "instruction_validation": "Аналізуй дані без Markdown. Поверни короткий текст."
        }
    def _format_metadata(self, metadata: dict) -> str:
        """Format metadata dictionary into readable text"""
        lines = []
        
        if "game_name" in metadata:
            lines.append(f"Game: {metadata['game_name']}")
        
        if "steam_game_info" in metadata:
            game_info = metadata['steam_game_info']
            lines.append(f"\nSteam Info:")
            lines.append(f"  Developers: {game_info.get('developers', 'N/A')}")
            lines.append(f"  Publishers: {game_info.get('publishers', 'N/A')}")
        
        if "urls_metadata" in metadata:
            lines.append(f"\nURL Analysis ({len(metadata['urls_metadata'])} URLs):")
            for idx, url_data in enumerate(metadata['urls_metadata'], 1):
                lines.append(f"\n  URL {idx}: {url_data.get('input_url')}")
                lines.append(f"    Domain: {url_data.get('domain')}")
                lines.append(f"    Country: {url_data.get('registrant_country') or url_data.get('country', 'Unknown')}")
                lines.append(f"    Registrar: {url_data.get('registrar', 'Unknown')}")
                lines.append(f"    Russian traces: {', '.join(url_data.get('russian_traces', []))}")
        
        return "\n".join(lines)
    def gemeni_generate_text(self, prompt: str) -> str:
        # Convert metadata dict to a formatted string
        if isinstance(prompt, dict):
            formatted_text = self._format_metadata(prompt)
        else:
            formatted_text = str(prompt) 
        
        text = f"""Інструкція: {self.prompt_data["instruction_validation"]} Текст: {formatted_text}"""
        return self.gemini_ai.generate_text(text)
    def openai_generate_text(self, prompt: str) -> str:   
        # Convert metadata dict to a formatted string
        if isinstance(prompt, dict):
            formatted_text = self._format_metadata(prompt)
        else:
            formatted_text = str(prompt) 
        text = [
            {"role": "system", "content":  self.prompt_data["instruction_validation"]},
            {"role": "user", "content": formatted_text}
        ]
        return self.openai_ai.generate_text(text)
    def run(self):
        print("AI Machine Main is running.")
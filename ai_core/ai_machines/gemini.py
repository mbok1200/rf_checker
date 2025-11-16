from google import genai
from google.genai import types
import time, random
from ..state_machine.state import State

class GeminiAI:
    def __init__(self):
        self.client = genai.Client()
        self.grounding = types.Tool(
            google_search=types.GoogleSearch()
        )
        self.state_machine = State()

    def generate_text(self, prompt: str) -> str:
        key_db = self.state_machine.metadata.get("game_name")
        
        if len(self.state_machine.metadata.get("urls_metadata")) > 0:
            if key_db is not None:
                key_db = "domain_check_" + self.state_machine.metadata.get("urls_metadata")[0]['domain'] + "_" + key_db
            else:
                key_db = "domain_check_" + self.state_machine.metadata.get("urls_metadata")[0]['domain']
        elif self.state_machine.metadata.get("text_detected") is not None:
            key_db = "general_check"

        key = self.state_machine.make_key(key_db)
        
        if key in self.state_machine.cache:
            return self.state_machine.cache[key]
        config = types.GenerateContentConfig(
            tools=[self.grounding],
            system_instruction="Відповідай звичайним текстом. Не використовуй Markdown, списки, заголовки чи кодові блоки.",
            response_mime_type="text/plain",
            max_output_tokens=512
        )
        range_try = 999
        for attempt in range(range_try):    
           try:
                response = self.client.models.generate_content(
                    model="gemini-2.5-flash",  # Try newer model
                    # OR: model="gemini-1.5-flash"  # More stable
                    contents=prompt,
                    config=config
                )
                self.state_machine.cache[key] = response.text
                
                return response.text
           except Exception as e:
                if "503" in str(e) or "UNAVAILABLE" in str(e):
                    if attempt < range_try - 1:
                        wait_time = (2 ** attempt) + random.uniform(0, 1)
                        print(f"Model overloaded, retrying in {wait_time:.1f}s...")
                        time.sleep(wait_time)
                        continue
                    else:
                        return f"Error: Gemini unavailable after {range_try} attempts. {str(e)}"
                else:
                    raise e
        return "Failed to generate text after multiple attempts."
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
        urls_metadata = self.state_machine.metadata.get("urls_metadata") or []
        
        if urls_metadata and len(urls_metadata) > 0:
            if key_db is not None:
                key_db = "domain_check_" + urls_metadata[0]['domain'] + "_" + key_db
            else:
                key_db = "domain_check_" + urls_metadata[0]['domain']
        elif self.state_machine.metadata.get("text_detected") is not None:
            key_db = "general_check"
        else:
            # Якщо немає ні URLs, ні text_detected
            key_db = "empty_check"

        key = self.state_machine.make_key(key_db)
        
        # if key in self.state_machine.cache:
        #     return self.state_machine.cache[key]
        config = types.GenerateContentConfig(
            tools=[self.grounding],
            system_instruction="Відповідай звичайним текстом. Не використовуй Markdown, списки, заголовки чи кодові блоки.",
            response_mime_type="text/plain",
            max_output_tokens=512
        )
        range_try = 8
        for attempt in range(range_try):
            try:
                response = self.client.models.generate_content(
                    model="gemini-2.5-flash",
                    contents=prompt,
                    config=config
                )
                # Багатоканальний витяг тексту
                raw_text = None

                if response is not None:
                    if getattr(response, "text", None):
                        raw_text = response.text
                    elif getattr(response, "candidates", None):
                        for c in response.candidates:
                            if hasattr(c, "content") and getattr(c.content, "parts", None):
                                for p in c.content.parts:
                                    if hasattr(p, "text") and p.text:
                                        raw_text = p.text
                                        break
                            if raw_text:
                                break

                if not raw_text or not raw_text.strip():
                    print(f"[Gemini] Порожня відповідь (attempt {attempt+1}) → retry")
                    if attempt < range_try - 1:
                        time.sleep(1.5 + random.uniform(0, 0.5))
                        continue
                    return "Error: empty response from Gemini."

                print(f"Gemini response (truncated): {raw_text[:200]}")
                self.state_machine.cache[key] = raw_text
                return raw_text

            except Exception as e:
                msg = str(e)
                if "503" in msg or "UNAVAILABLE" in msg:
                    if attempt < range_try - 1:
                        wait_time = (2 ** attempt) + random.uniform(0, 0.5)
                        print(f"[Gemini] Overloaded, retry in {wait_time:.1f}s")
                        time.sleep(wait_time)
                        continue
                    return f"Error: Gemini unavailable after {range_try} attempts. {msg}"
                raise
        return "Failed to generate text after retries."
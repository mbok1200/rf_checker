from openai import OpenAI
import os
class OpenAIMachine:
    def __init__(self):
        self.client = OpenAI(
            base_url="https://openrouter.ai/api/v1",
            api_key=os.getenv("OPENROUTER_API_KEY"),
        )

    def generate_text(self, prompt: list) -> str:
        completion = self.client.chat.completions.create(
            model="mistralai/mistral-7b-instruct:free",
            messages=prompt,
            max_tokens=512,
        )
        return completion.choices[0].message.content
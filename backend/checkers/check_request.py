from pydantic import BaseModel, field_validator, Field, model_validator
class CheckRequest(BaseModel):
    urls: list[str] = Field(default=[], max_items=10)  # Макс 10 URL
    game_name: str | None = Field(None, max_length=500)
    @model_validator(mode='after')
    def check_at_least_one_field(self):
        if not self.urls and not self.game_name:
            raise ValueError('At least one of "urls" or "game_name" must be provided')
        return self
    @field_validator('urls')
    def validate_urls(cls, v):
            # raise ValueError('At least one URL required')
        for url in v:
            if len(url) > 500:
                raise ValueError('URL too long')
            # Базова перевірка на SQL injection
            if any(x in url.lower() for x in ['<script', 'javascript:', 'onerror=']):
                raise ValueError('Invalid URL format')
        return v
    
    @field_validator('game_name')
    def validate_game_name(cls, v):
        dangerous = ['<script', '</script', 'javascript:', 'onerror=', 
                        'union select', 'drop table', '--', ';--']
        if v and any(x in v.lower() for x in dangerous):
            raise ValueError('Invalid game name')
        return v
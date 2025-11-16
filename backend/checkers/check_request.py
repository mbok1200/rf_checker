from pydantic import BaseModel, field_validator, Field
class CheckRequest(BaseModel):
    urls: list[str] = Field(..., max_items=10)  # Макс 10 URL
    game_name: str | None = Field(None, max_length=100)
    
    @field_validator('urls')
    def validate_urls(cls, v):
        if not v:
            return v
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
        if v and any(x in v.lower() for x in ['<', '>', 'script', 'union', 'select']):
            raise ValueError('Invalid game name')
        return v
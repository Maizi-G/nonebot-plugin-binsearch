from pydantic import BaseModel


class Config(BaseModel):
    bin_api_key: str

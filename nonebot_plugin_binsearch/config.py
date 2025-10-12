from pydantic import BaseModel, field_validator
from typing import Union, List

class Config(BaseModel):
    bin_api_key: Union[str, List[str]]
    ignore_user_ids: list[str] = [3938088854]

    @field_validator("bin_api_key", mode="before")
    def ensure_list(cls, v):
        if isinstance(v, str):
            # 支持逗号分隔或单字符串
            return [key.strip() for key in v.split(",") if key.strip()]
        elif isinstance(v, list):
            return v
        else:
            raise TypeError("bin_api_key 必须是字符串或字符串列表")



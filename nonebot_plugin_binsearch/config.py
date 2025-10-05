from pydantic import BaseModel


class Config(BaseModel):
    bin_api_key: str
    # 忽略的 QQ 用户 ID 列表（字符串或数字均可）
    ignore_user_ids: list[str] = [3938088854]

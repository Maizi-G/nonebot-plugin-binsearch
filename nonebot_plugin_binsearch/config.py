from pydantic import BaseModel, Field, field_validator


class Config(BaseModel):
    bin_api_key: list[str]
    ignore_user_ids: list[str] = Field(default_factory=lambda: ["3938088854"])
    bin_user_cooldown: int = 10
    bin_group_cooldown: int = 3

    @field_validator("bin_api_key", mode="before")
    @classmethod
    def ensure_list(cls, v):
        if isinstance(v, str):
            # 支持逗号分隔或单字符串
            keys = [key.strip() for key in v.split(",") if key.strip()]
        elif isinstance(v, list):
            keys = [str(key).strip() for key in v if str(key).strip()]
        else:
            raise TypeError("bin_api_key 必须是字符串或字符串列表")

        if not keys:
            raise ValueError("bin_api_key 不能为空")
        return keys

    @field_validator("ignore_user_ids", mode="before")
    @classmethod
    def ensure_ignore_user_ids(cls, v):
        if v is None:
            return []
        if isinstance(v, (str, int)):
            return [str(v)]
        if isinstance(v, list):
            return [str(uid) for uid in v]
        raise TypeError("ignore_user_ids 必须是字符串、数字或列表")

    @field_validator("bin_user_cooldown", "bin_group_cooldown", mode="before")
    @classmethod
    def ensure_non_negative_int(cls, v):
        if v is None:
            return 0
        value = int(v)
        if value < 0:
            raise ValueError("冷却时间不能小于 0")
        return value



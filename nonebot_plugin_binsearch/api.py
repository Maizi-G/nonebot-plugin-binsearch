import httpx
from nonebot import get_plugin_config
from .config import Config

config = get_plugin_config(Config)

async def query_bin_info(bin_number: str):
    url = "https://bin-ip-checker.p.rapidapi.com/"
    headers = {
        "Content-Type": "application/json",
        "x-rapidapi-key": config.bin_api_key,
        "x-rapidapi-host": "bin-ip-checker.p.rapidapi.com",
    }
    query_params = {"bin": bin_number}
    json_payload = {"bin": bin_number}
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                url, headers=headers, params=query_params, json=json_payload
            )
            response.raise_for_status()
            return response.json()
    except Exception:
        raise

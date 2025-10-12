import httpx
import itertools
import threading
from nonebot import get_plugin_config
from .config import Config

config = get_plugin_config(Config)

#多apikey负载均衡
api_keys = config.bin_api_key
_cycle = itertools.cycle(api_keys)
_lock = threading.Lock()

def get_next_key():
    with _lock:
        return next(_cycle)

async def query_bin_info(bin_number: str):
    url = "https://bin-ip-checker.p.rapidapi.com/"
    headers = {
        "Content-Type": "application/json",
        "x-rapidapi-key": get_next_key(),
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

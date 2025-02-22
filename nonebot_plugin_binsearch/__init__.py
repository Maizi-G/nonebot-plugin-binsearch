import httpx
from nonebot import on_command
from nonebot.adapters.onebot.v11 import Message, Bot, Event
from nonebot.params import CommandArg
from nonebot.plugin import PluginMetadata
from pydantic import BaseModel
from nonebot import get_plugin_config
from .config import Config

__plugin_meta__ = PluginMetadata(
    name="卡bin查询",
    description="用于查询信用卡的卡组织，卡等级，卡类型，发卡国等",
    homepage="https://github.com/bankcarddev/nonebot-plugin-binsearch",
    usage="/bin 533228",
    type="application",
    config=Config,
    supported_adapters={"~onebot.v11"},
)

config = get_plugin_config(Config)

async def query_bin_info(bin_number: str):
    url = "https://bin-ip-checker.p.rapidapi.com/"
    headers = {
        "x-rapidapi-key": config.bin_api_key,
        "x-rapidapi-host": "bin-ip-checker.p.rapidapi.com",
        "Content-Type": "application/json"
    }
    params = {"bin": bin_number}
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(url, headers=headers, params=params)
            response.raise_for_status()
            return response.json()
    except httpx.HTTPError as e:
        raise Exception(f"API请求失败: {str(e)}")
    except Exception as e:
        raise Exception(f"发生未知错误: {str(e)}")

bin_query = on_command('bin', aliases={'bin查询'}, priority=5)

@bin_query.handle()
async def handle_bin_query(bot: Bot, event: Event, arg: Message = CommandArg()):
    bin_number = arg.extract_plain_text().strip()
    if not bin_number.isdigit() or len(bin_number) != 6:
        await bot.send(event, "🚫 请输入6位数字卡BIN，例如：/bin 448590")
        return
    
    try:
        result = await query_bin_info(bin_number)
        if result.get('success', False):
            bin_data = result['BIN']
            issuer_website = bin_data['issuer']['website'] if bin_data['issuer']['website'] else "暂无"
            reply = (
                f"🔍 卡BIN信息查询结果：\n"
                f"├ 卡号段：{bin_data['number']}\n"
                f"├ 卡组织：{bin_data['scheme']}\n"
                f"├ 卡类型：{bin_data['type']}\n"
                f"├ 卡等级：{bin_data['level']}\n"
                f"├ 商用卡：{'✅ 是' if bin_data.get('is_commercial') == 'true' else '❌ 否'}\n"
                f"├ 预付卡：{'✅ 是' if bin_data.get('is_prepaid') == 'true' else '❌ 否'}\n"
                f"├ 发卡国：{bin_data['country']['name']} {bin_data['country']['flag']} ({bin_data['country']['alpha2']})\n"
                f"├ 发卡行：{bin_data['issuer']['name']}\n"
                f"├ 银行网站：{issuer_website}\n"
                f"└ 默认币种：{bin_data['currency']}"
            )
            await bot.send(event, Message(reply))
        else:
            await bot.send(event, "⚠️ 查询失败，请检查BIN号是否正确或稍后重试。")
    except Exception as e:
        await bot.send(event, f"❌ 查询时发生错误：{str(e)}")
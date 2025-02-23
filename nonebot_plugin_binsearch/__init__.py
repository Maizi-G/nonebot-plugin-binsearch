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
            issuer_website = bin_data['issuer']['website'] or "暂无"
            prepaid_icon = "✅" if bin_data.get('is_prepaid') == 'true' else "❌"
            commercial_icon = "✅" if bin_data.get('is_commercial') == 'true' else "❌"
            
            reply = (
                f"💳【卡BIN查询结果】{bin_number}\n"
                f"══════════════════\n"
                f"▸ 卡号段：{bin_data['number']}\n"
                f"▸ 卡组织：{bin_data['scheme']}\n"
                f"▸ 卡片类型：{bin_data['type']} {bin_data['level']}\n"
                f"▸ 预付卡：{prepaid_icon} ｜ 商用卡：{commercial_icon}\n"
                f"\n🌍【发行信息】\n"
                f"══════════════════\n"
                f"▸ 国家：{bin_data['country']['flag']} {bin_data['country']['name']}\n"
                f"▸ 代码：{bin_data['country']['alpha2']}\n"
                f"▸ 货币：{bin_data['currency']}\n"
                f"\n🏦【发卡机构】\n"
                f"══════════════════\n"
                f"▸ 银行名称：{bin_data['issuer']['name']}\n"
                f"▸ 官方网站：{issuer_website}\n"
                
            )
            await bot.send(event, Message(reply))
        else:
            await bot.send(event, "⚠️ 查询失败，请检查BIN号是否正确或稍后重试。")
    except Exception as e:
        await bot.send(event, f"❌ 查询时发生错误：{str(e)}")
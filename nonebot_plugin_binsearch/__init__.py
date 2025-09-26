from nonebot import on_command, get_plugin_config

from nonebot.plugin import PluginMetadata
from .config import Config

from nonebot.adapters.onebot.v11 import Bot, Event, Message, MessageSegment
from nonebot.params import CommandArg

from .main_bin import result_527375
from .refused_bin import refused_bin_list
from nonebot.exception import FinishedException
from .api import query_bin_info
from .image import create_bin_image

__plugin_meta__ = PluginMetadata(
    name="卡bin查询",
    description="用于查询信用卡的卡组织，卡等级，卡类型，发卡国家或地区等 (图片版)",
    homepage="https://github.com/bankcarddev/nonebot-plugin-binsearch",
    usage="/bin 533228",
    type="application",
    config=Config,
    supported_adapters={"~onebot.v11"},
)

bin_query = on_command('bin', aliases={'BIN','Bin'}, priority=5, block=True)

@bin_query.handle()
async def handle_bin_query(bot: Bot, event: Event, arg: Message = CommandArg()):
    bin_number = arg.extract_plain_text().strip()

    if not bin_number:
        await bot.send(event, "📌 请输入卡BIN，例如：/bin 448590")
        return
    if not bin_number.isdigit() or not (6 <= len(bin_number) <= 8):
        await bot.send(event, "🚫 卡BIN通常是6到8位数字，例如：/bin 448590")
        return
        # 🚫 黑名单检测
    if bin_number in refused_bin_list:
        await bot.send(event, f"❌ 该 BIN（{bin_number}）已被禁止查询。")
        return

    try:
        if bin_number == '527375':
            result = result_527375
        else:
            result = await query_bin_info(bin_number)

        if result.get('success') and result.get('BIN'):
            image_bytes = create_bin_image(bin_number, result)
            await bot.send(event,MessageSegment.image(image_bytes))
        else:
            await bin_query.finish("⚠️ 查询失败，可能该Bin不存在或网络出现问题。")

    except FinishedException:
        # 让 finish() 正常工作，不要拦截它
        raise
    except Exception as e:
        # 其他异常才捕获
        await bin_query.finish("⚠️ 查询失败，可能该Bin不存在或网络出现问题。")

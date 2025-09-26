from nonebot.adapters.onebot.v11 import Bot, Event, Message, MessageSegment
from nonebot.params import CommandArg

from .refused_bin import refused_bin_list
from .api import query_bin_info
from .image import create_bin_image

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
        result = await query_bin_info(bin_number)
        if result.get('success', False) and result.get('BIN'):
            image_bytes = create_bin_image(bin_number, result)
            await bot.send(event, MessageSegment.image(image_bytes))
        else:
            await bot.send(event, "⚠️ 查询失败，请稍后再试。")
    except Exception:
        await bot.send(event, "❌ 查询失败，请稍后再试。")

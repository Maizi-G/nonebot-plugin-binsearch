import time
from typing import Optional

from nonebot import get_plugin_config, on_command
from nonebot.adapters.onebot.v11 import Bot, Event, Message, MessageSegment
from nonebot.exception import FinishedException
from nonebot.log import logger
from nonebot.params import CommandArg
from nonebot.plugin import PluginMetadata

from .api import query_bin_info
from .config import Config
from .image import create_bin_image
from .main_bin import result_527375
from .refused_bin import refused_bin_list

# 读取插件配置
plugin_config = get_plugin_config(Config)

_user_last_query_at: dict[str, float] = {}
_group_last_query_at: dict[str, float] = {}

__plugin_meta__ = PluginMetadata(
    name="卡bin查询",
    description="用于查询信用卡的卡组织，卡等级，卡类型，发卡国家或地区等 (图片版)",
    homepage="https://github.com/bankcarddev/nonebot-plugin-binsearch",
    usage="/bin 533228",
    type="application",
    config=Config,
    supported_adapters={"~onebot.v11"},
)

bin_query = on_command("bin", aliases={"BIN", "Bin"}, priority=5, block=True)


def _format_remaining(seconds: float) -> int:
    return max(1, int(seconds + 0.999))


def _check_and_update_cooldown(user_id: str, group_id: Optional[str]) -> Optional[str]:
    now = time.monotonic()
    user_cooldown = plugin_config.bin_user_cooldown
    group_cooldown = plugin_config.bin_group_cooldown

    if user_cooldown > 0:
        elapsed = now - _user_last_query_at.get(user_id, 0)
        if elapsed < user_cooldown:
            remaining = _format_remaining(user_cooldown - elapsed)
            return f"⏳ 查询太频繁啦，请 {remaining} 秒后再试。"

    if group_id and group_cooldown > 0:
        elapsed = now - _group_last_query_at.get(group_id, 0)
        if elapsed < group_cooldown:
            remaining = _format_remaining(group_cooldown - elapsed)
            return f"⏳ 本群查询太频繁啦，请 {remaining} 秒后再试。"

    _user_last_query_at[user_id] = now
    if group_id:
        _group_last_query_at[group_id] = now
    return None


@bin_query.handle()
async def handle_bin_query(bot: Bot, event: Event, arg: Message = CommandArg()):
    # 忽略来自配置中的用户ID
    user_id = event.get_user_id()
    ignore_ids = {str(uid) for uid in getattr(plugin_config, "ignore_user_ids", [])}
    if user_id in ignore_ids:
        return
    bin_number = arg.extract_plain_text().strip()

    if not bin_number:
        await bot.send(event, "📌 请输入卡BIN，例如：/bin 448590")
        return
    if not bin_number.isdigit():
        await bin_query.finish()
        return
    if not (6 <= len(bin_number) <= 8):
        await bot.send(event, "🚫 卡BIN通常是6到8位数字，例如：/bin 448590")
        return

    # 🚫 黑名单检测
    if bin_number in refused_bin_list:
        await bot.send(event, "乱查唧唧短20cm😋")
        return

    group_id = getattr(event, "group_id", None)
    cooldown_message = _check_and_update_cooldown(
        user_id, str(group_id) if group_id is not None else None
    )
    if cooldown_message:
        await bot.send(event, cooldown_message)
        return

    try:
        if bin_number == "527375":
            result = result_527375
        else:
            result = await query_bin_info(bin_number)

        if result.get("success") and result.get("BIN"):
            image_bytes = create_bin_image(bin_number, result)
            await bot.send(event, MessageSegment.image(image_bytes))
        else:
            await bin_query.finish("⚠️ 查询失败，可能该Bin不存在或网络出现问题。")

    except FinishedException:
        # 让 finish() 正常工作，不要拦截它
        raise
    except Exception as exc:
        logger.exception("BIN 查询失败: %s", exc)
        # 其他异常才捕获
        await bin_query.finish("⚠️ 查询失败，可能该Bin不存在或网络出现问题。")

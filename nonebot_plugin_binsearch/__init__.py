from nonebot import on_command, get_plugin_config
from nonebot.adapters.onebot.v11 import Message, Bot, Event, MessageSegment
from nonebot.params import CommandArg
from nonebot.plugin import PluginMetadata
from .config import Config
from .handlers import handle_bin_query

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
async def _(bot: Bot, event: Event, arg: Message = CommandArg()):
    await handle_bin_query(bot, event, arg)

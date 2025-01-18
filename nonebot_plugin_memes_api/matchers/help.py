from datetime import datetime, timedelta, timezone

from nonebot.log import logger
from nonebot_plugin_alconna import Image, Text, on_alconna
from nonebot_plugin_uninfo import Uninfo

from ..api import MemeProperties, render_meme_list
from ..config import memes_config
from ..exception import MemeGeneratorException
from ..manager import meme_manager
from ..recorder import SessionIdType, get_meme_generation_keys
from .utils import UserId

help_matcher = on_alconna(
    "表情包制作",
    aliases={"表情列表", "表情包列表", "头像表情包", "文字表情包"},
    block=True,
    priority=11,
    use_cmd_start=True,
)


@help_matcher.handle()
async def _(user_id: UserId, session: Uninfo):
    memes = meme_manager.get_memes()
    list_image_config = memes_config.memes_list_image_config

    label_new_timedelta = list_image_config.label_new_timedelta
    label_hot_threshold = list_image_config.label_hot_threshold
    label_hot_days = list_image_config.label_hot_days

    meme_generation_keys = await get_meme_generation_keys(
        session,
        SessionIdType.GLOBAL,
        time_start=datetime.now(timezone.utc) - timedelta(days=label_hot_days),
    )

    meme_properties: dict[str, MemeProperties] = {}
    for meme in memes:
        new = datetime.now(timezone.utc) - meme.info.date_created < label_new_timedelta
        hot = meme_generation_keys.count(meme.key) >= label_hot_threshold
        disabled = not meme_manager.check(user_id, meme.key)
        properties = MemeProperties(disabled=disabled, hot=hot, new=new)
        meme_properties[meme.key] = properties

    try:
        output = await render_meme_list(
            meme_properties=meme_properties,
            exclude_memes=memes_config.memes_disabled_list,
            sort_by=list_image_config.sort_by,
            sort_reverse=list_image_config.sort_reverse,
            text_template=list_image_config.text_template,
            add_category_icon=list_image_config.add_category_icon,
        )
    except MemeGeneratorException as e:
        logger.warning(f"表情列表图生成失败：{e}")
        return

    msg = Text(
        "触发方式：“关键词 + 图片/文字/@某人”\n"
        "发送 “表情详情 + 关键词” 查看表情参数和预览\n"
        "目前支持的表情列表："
    ) + Image(raw=output)
    await msg.finish()

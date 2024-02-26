import asyncio
import hashlib
import random
import traceback
from itertools import chain
from typing import Any, Dict, List, NoReturn, Type

from nonebot import on_command, on_message, require
from nonebot.adapters import Message
from nonebot.exception import AdapterException
from nonebot.log import logger
from nonebot.matcher import Matcher
from nonebot.params import CommandArg
from nonebot.permission import SUPERUSER, Permission
from nonebot.plugin import PluginMetadata, inherit_supported_adapters
from nonebot.typing import T_Handler, T_State
from pypinyin import Style, pinyin
from typing_extensions import Annotated

require("nonebot_plugin_alconna")
require("nonebot_plugin_session")
require("nonebot_plugin_userinfo")
require("nonebot_plugin_localstore")

from nonebot_plugin_alconna import Image, Text, UniMessage
from nonebot_plugin_localstore import get_cache_dir
from nonebot_plugin_session import EventSession, SessionId, SessionIdType, SessionLevel
from nonebot_plugin_userinfo import ImageSource, UserInfo

from .config import Config, memes_config
from .depends import IMAGE_SOURCES_KEY, TEXTS_KEY, USER_INFOS_KEY, split_msg
from .exception import (
    ArgMismatch,
    ArgParserExit,
    MemeGeneratorException,
    NetworkError,
    PlatformUnsupportError,
    TextOrNameNotEnough,
    TextOverLength,
)
from .manager import ActionResult, MemeMode, meme_manager
from .request import (
    MemeInfo,
    MemeKeyWithProperties,
    RenderMemeListRequest,
    generate_meme,
    generate_meme_preview,
    parse_meme_args,
    render_meme_list,
)
from .rule import command_rule, regex_rule
from .utils import meme_info

__plugin_meta__ = PluginMetadata(
    name="表情包制作",
    description="制作各种沙雕表情包",
    usage="发送“表情包制作”查看表情包列表",
    type="application",
    homepage="https://github.com/noneplugin/nonebot-plugin-memes-api",
    config=Config,
    supported_adapters=inherit_supported_adapters(
        "nonebot_plugin_alconna",
        "nonebot_plugin_session",
        "nonebot_plugin_userinfo",
    ),
    extra={
        "unique_name": "memes_api",
        "author": "meetwq <meetwq@gmail.com>",
        "version": "0.3.0",
    },
)

memes_cache_dir = get_cache_dir("nonebot_plugin_memes_api")


def _is_private(session: EventSession) -> bool:
    return session.level == SessionLevel.LEVEL1


PERM_EDIT = SUPERUSER | Permission(_is_private)
PERM_GLOBAL = SUPERUSER


try:
    from nonebot.adapters.onebot.v11.permission import GROUP_ADMIN, GROUP_OWNER

    PERM_EDIT |= GROUP_ADMIN | GROUP_OWNER
except ImportError:
    pass


help_cmd = on_command(
    "表情包制作", aliases={"头像表情包", "文字表情包"}, block=True, priority=11
)
info_cmd = on_command(
    "表情详情", aliases={"表情帮助", "表情示例"}, block=True, priority=11
)
block_cmd = on_command("禁用表情", block=True, priority=11, permission=PERM_EDIT)
unblock_cmd = on_command("启用表情", block=True, priority=11, permission=PERM_EDIT)
block_cmd_gl = on_command(
    "全局禁用表情", block=True, priority=11, permission=PERM_GLOBAL
)
unblock_cmd_gl = on_command(
    "全局启用表情", block=True, priority=11, permission=PERM_GLOBAL
)


UserId = Annotated[str, SessionId(SessionIdType.GROUP, include_bot_type=False)]


@help_cmd.handle()
async def _(user_id: UserId):
    memes = sorted(
        meme_manager.memes,
        key=lambda meme: "".join(
            chain.from_iterable(pinyin(meme.keywords[0], style=Style.TONE3))
        ),
    )
    meme_list = [
        MemeKeyWithProperties(
            meme_key=meme.key,
            fill="black" if meme_manager.check(user_id, meme.key) else "lightgrey",
        )
        for meme in memes
    ]

    # cache rendered meme list
    meme_list_hashable = [
        ({"key": meme.key, "keywords": meme.keywords}, prop)
        for meme, prop in zip(memes, meme_list)
    ]
    meme_list_hash = hashlib.md5(str(meme_list_hashable).encode("utf8")).hexdigest()
    meme_list_cache_file = memes_cache_dir / f"{meme_list_hash}.jpg"
    if not meme_list_cache_file.exists():
        img = await render_meme_list(RenderMemeListRequest(meme_list=meme_list))
        with open(meme_list_cache_file, "wb") as f:
            f.write(img)
    else:
        img = meme_list_cache_file.read_bytes()

    msg = Text(
        "触发方式：“关键词 + 图片/文字”\n"
        "发送 “表情详情 + 关键词” 查看表情参数和预览\n"
        "目前支持的表情列表："
    ) + Image(raw=img)
    await msg.send()


@info_cmd.handle()
async def _(matcher: Matcher, arg: Message = CommandArg()):
    meme_name = arg.extract_plain_text().strip()
    if not meme_name:
        matcher.block = False
        await matcher.finish()

    if not (meme := meme_manager.find(meme_name)):
        await matcher.finish(f"表情 {meme_name} 不存在！")

    info = await meme_info(meme)
    info += "表情预览：\n"
    img = await generate_meme_preview(meme.key)

    msg = Text(info) + Image(raw=img)
    await msg.send()


@block_cmd.handle()
async def _(matcher: Matcher, user_id: UserId, arg: Message = CommandArg()):
    meme_names = arg.extract_plain_text().strip().split()
    if not meme_names:
        matcher.block = False
        await matcher.finish()
    results = meme_manager.block(user_id, meme_names)
    messages = []
    for name, result in results.items():
        if result == ActionResult.SUCCESS:
            message = f"表情 {name} 禁用成功"
        elif result == ActionResult.NOTFOUND:
            message = f"表情 {name} 不存在！"
        else:
            message = f"表情 {name} 禁用失败"
        messages.append(message)
    await matcher.finish("\n".join(messages))


@unblock_cmd.handle()
async def _(matcher: Matcher, user_id: UserId, arg: Message = CommandArg()):
    meme_names = arg.extract_plain_text().strip().split()
    if not meme_names:
        matcher.block = False
        await matcher.finish()
    results = meme_manager.unblock(user_id, meme_names)
    messages = []
    for name, result in results.items():
        if result == ActionResult.SUCCESS:
            message = f"表情 {name} 启用成功"
        elif result == ActionResult.NOTFOUND:
            message = f"表情 {name} 不存在！"
        else:
            message = f"表情 {name} 启用失败"
        messages.append(message)
    await matcher.finish("\n".join(messages))


@block_cmd_gl.handle()
async def _(matcher: Matcher, arg: Message = CommandArg()):
    meme_names = arg.extract_plain_text().strip().split()
    if not meme_names:
        matcher.block = False
        await matcher.finish()
    results = meme_manager.change_mode(MemeMode.WHITE, meme_names)
    messages = []
    for name, result in results.items():
        if result == ActionResult.SUCCESS:
            message = f"表情 {name} 已设为白名单模式"
        elif result == ActionResult.NOTFOUND:
            message = f"表情 {name} 不存在！"
        else:
            message = f"表情 {name} 设置失败"
        messages.append(message)
    await matcher.finish("\n".join(messages))


@unblock_cmd_gl.handle()
async def _(matcher: Matcher, arg: Message = CommandArg()):
    meme_names = arg.extract_plain_text().strip().split()
    if not meme_names:
        matcher.block = False
        await matcher.finish()
    results = meme_manager.change_mode(MemeMode.BLACK, meme_names)
    messages = []
    for name, result in results.items():
        if result == ActionResult.SUCCESS:
            message = f"表情 {name} 已设为黑名单模式"
        elif result == ActionResult.NOTFOUND:
            message = f"表情 {name} 不存在！"
        else:
            message = f"表情 {name} 设置失败"
        messages.append(message)
    await matcher.finish("\n".join(messages))


async def process(
    matcher: Matcher,
    meme: MemeInfo,
    image_sources: List[ImageSource],
    texts: List[str],
    user_infos: List[UserInfo],
    args: Dict[str, Any] = {},
):
    images: List[bytes] = []

    try:
        for image_source in image_sources:
            images.append(await image_source.get_image())
    except PlatformUnsupportError as e:
        await matcher.finish(
            f"当前平台 “{e.platform}” 暂不支持获取头像，请使用图片输入"
        )
    except (NetworkError, AdapterException):
        logger.warning(traceback.format_exc())
        await matcher.finish("图片下载出错，请稍后再试")

    args_user_infos = []
    for user_info in user_infos:
        name = user_info.user_displayname or user_info.user_name
        gender = str(user_info.user_gender)
        if gender not in ("male", "female"):
            gender = "unknown"
        args_user_infos.append({"name": name, "gender": gender})
    args["user_infos"] = args_user_infos

    try:
        result = await generate_meme(meme.key, images=images, texts=texts, args=args)
    except TextOverLength:
        await matcher.finish("文字长度过长")
    except ArgMismatch:
        await matcher.finish("参数解析错误")
    except TextOrNameNotEnough:
        await matcher.finish("文字或名字数量不足")
    except MemeGeneratorException:
        logger.warning(traceback.format_exc())
        await matcher.finish("出错了，请稍后再试")

    msg = UniMessage.image(raw=result)
    await msg.send()


def handler(meme: MemeInfo) -> T_Handler:
    async def handle(state: T_State, matcher: Matcher, user_id: UserId):
        if not meme_manager.check(user_id, meme.key):
            return

        raw_texts: List[str] = state[TEXTS_KEY]
        user_infos: List[UserInfo] = state[USER_INFOS_KEY]
        image_sources: List[ImageSource] = state[IMAGE_SOURCES_KEY]

        texts: List[str] = []
        args: Dict[str, Any] = {}

        async def finish(msg: str) -> NoReturn:
            logger.info(msg)
            if memes_config.memes_prompt_params_error:
                matcher.stop_propagation()
                await matcher.finish(msg)
            await matcher.finish()

        if meme.params.args:
            try:
                parse_result = await parse_meme_args(meme.key, raw_texts)
            except ArgParserExit:
                logger.warning(traceback.format_exc())
                await finish("参数解析错误")
            texts = parse_result["texts"]
            parse_result.pop("texts")
            args = parse_result
        else:
            texts = raw_texts

        if not (meme.params.min_images <= len(image_sources) <= meme.params.max_images):
            await finish(
                f"输入图片数量不符，图片数量应为 {meme.params.min_images}"
                + (
                    f" ~ {meme.params.max_images}"
                    if meme.params.max_images > meme.params.min_images
                    else ""
                )
            )
        if not (meme.params.min_texts <= len(texts) <= meme.params.max_texts):
            await finish(
                f"输入文字数量不符，文字数量应为 {meme.params.min_texts}"
                + (
                    f" ~ {meme.params.max_texts}"
                    if meme.params.max_texts > meme.params.min_texts
                    else ""
                )
            )

        matcher.stop_propagation()
        await process(matcher, meme, image_sources, texts, user_infos, args)

    return handle


async def random_handler(state: T_State, matcher: Matcher):
    texts: List[str] = state[TEXTS_KEY]
    user_infos: List[UserInfo] = state[USER_INFOS_KEY]
    image_sources: List[ImageSource] = state[IMAGE_SOURCES_KEY]

    random_meme = random.choice(
        [
            meme
            for meme in meme_manager.memes
            if (
                (meme.params.min_images <= len(image_sources) <= meme.params.max_images)
                and (meme.params.min_texts <= len(texts) <= meme.params.max_texts)
            )
        ]
    )
    await process(matcher, random_meme, image_sources, texts, user_infos)


random_matcher = on_message(command_rule(["随机表情"]), block=False, priority=12)
fake_meme = MemeInfo(key="_fake")
random_matcher.append_handler(random_handler, parameterless=[split_msg(fake_meme)])


matchers: Dict[str, List[Type[Matcher]]] = {}


def create_matchers():
    for meme in meme_manager.memes:
        matchers[meme.key] = []
        if meme.keywords:
            matchers[meme.key].append(
                on_message(command_rule(meme.keywords), block=False, priority=12)
            )
        if meme.patterns:
            matchers[meme.key].append(
                on_message(regex_rule(meme.patterns), block=False, priority=13)
            )

        for matcher in matchers[meme.key]:
            matcher.append_handler(handler(meme), parameterless=[split_msg(meme)])


def destroy_matchers():
    for _, meme_matchers in matchers.items():
        for meme_matcher in meme_matchers:
            meme_matcher.destroy()
    matchers.clear()


refresh_matcher = on_message(
    command_rule(["刷新表情", "更新表情"]), block=True, priority=11
)


@refresh_matcher.handle()
async def _(matcher: Matcher):
    destroy_matchers()
    await meme_manager.init()
    create_matchers()
    await matcher.finish("表情更新成功")


from nonebot import get_driver

driver = get_driver()


async def init():
    await meme_manager.init()
    create_matchers()


@driver.on_startup
async def _():
    asyncio.create_task(init())

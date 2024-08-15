import json
from datetime import datetime
from typing import Any, Literal, Optional, Union, cast, overload

import httpx
from arclet.alconna import ArgFlag, Args, Empty, Option
from arclet.alconna.action import Action
from nonebot.compat import model_dump, type_validate_python
from pydantic import BaseModel

from .config import memes_config
from .exception import (
    ArgMismatch,
    ArgModelMismatch,
    ArgParserMismatch,
    ImageNumberMismatch,
    MemeFeedback,
    MemeGeneratorException,
    NoSuchMeme,
    OpenImageFailed,
    ParamsMismatch,
    TextNumberMismatch,
    TextOrNameNotEnough,
    TextOverLength,
)

BASE_URL = memes_config.meme_generator_base_url


@overload
async def send_request(
    router: str,
    request_type: Literal["POST", "GET"],
    response_type: Literal["JSON"],
    **kwargs,
) -> Union[dict[str, Any], list[Any]]: ...


@overload
async def send_request(
    router: str,
    request_type: Literal["POST", "GET"],
    response_type: Literal["BYTES"],
    **kwargs,
) -> bytes: ...


@overload
async def send_request(
    router: str,
    request_type: Literal["POST", "GET"],
    response_type: Literal["TEXT"],
    **kwargs,
) -> str: ...


async def send_request(
    router: str,
    request_type: Literal["POST", "GET"],
    response_type: Literal["JSON", "BYTES", "TEXT"],
    **kwargs,
):
    async with httpx.AsyncClient(timeout=300) as client:
        request_method = client.post if request_type == "POST" else client.get
        resp = await request_method(BASE_URL + router, **kwargs)
        status_code = resp.status_code
        if status_code == 200:
            if response_type == "JSON":
                return resp.json()
            elif response_type == "BYTES":
                return resp.content
            else:
                return resp.text
        elif 520 <= status_code < 600:
            message = resp.json()["detail"]
            if 560 <= status_code < 570:
                raise MemeFeedback(message)
            elif status_code == 551:
                raise ArgParserMismatch(message)
            elif status_code == 552:
                raise ArgModelMismatch(message)
            elif 550 <= status_code < 560:
                raise ArgMismatch(message)
            elif status_code == 541:
                raise ImageNumberMismatch(message)
            elif status_code == 542:
                raise TextNumberMismatch(message)
            elif status_code == 543:
                raise TextOrNameNotEnough(message)
            elif 540 <= status_code < 550:
                raise ParamsMismatch(message)
            elif status_code == 531:
                raise NoSuchMeme(message)
            elif status_code == 532:
                raise TextOverLength(message)
            elif status_code == 533:
                raise OpenImageFailed(message)
            else:
                raise MemeGeneratorException(message)


class MemeKeyWithProperties(BaseModel):
    meme_key: str
    disabled: bool = False
    labels: list[Literal["new", "hot"]] = []


class RenderMemeListRequest(BaseModel):
    meme_list: list[MemeKeyWithProperties]
    text_template: str = "{keywords}"
    add_category_icon: bool = True


async def render_meme_list(
    meme_list: list[MemeKeyWithProperties],
    *,
    text_template: str = "{keywords}",
    add_category_icon: bool = True,
) -> bytes:
    return await send_request(
        "/memes/render_list",
        "POST",
        "BYTES",
        json=model_dump(
            RenderMemeListRequest(
                meme_list=meme_list,
                text_template=text_template,
                add_category_icon=add_category_icon,
            )
        ),
    )


async def get_meme_keys() -> list[str]:
    return cast(list[str], await send_request("/memes/keys", "GET", "JSON"))


class ParserArg(BaseModel):
    name: str
    value: str
    default: Optional[Any] = None
    flags: Optional[list[ArgFlag]] = None


class ParserOption(BaseModel):
    names: list[str]
    args: Optional[list[ParserArg]] = None
    dest: Optional[str] = None
    default: Optional[Any] = None
    action: Optional[Action] = None
    help_text: Optional[str] = None
    compact: bool = False

    def option(self) -> Option:
        args = Args()
        for arg in self.args or []:
            args.add(
                name=arg.name,
                value=arg.value,
                default=arg.default or Empty,
                flags=arg.flags,
            )

        return Option(
            name="|".join(self.names),
            args=args,
            dest=self.dest,
            default=self.default,
            action=self.action,
            help_text=self.help_text,
            compact=self.compact,
        )


class CommandShortcut(BaseModel):
    key: str
    args: Optional[list[str]] = None
    humanized: Optional[str] = None


class MemeArgsType(BaseModel):
    args_model: dict[str, Any]
    args_examples: list[dict[str, Any]]
    parser_options: list[ParserOption]


class MemeParamsType(BaseModel):
    min_images: int
    max_images: int
    min_texts: int
    max_texts: int
    default_texts: list[str]
    args_type: Optional[MemeArgsType] = None


class MemeInfo(BaseModel):
    key: str
    params_type: MemeParamsType
    keywords: list[str]
    shortcuts: list[CommandShortcut]
    tags: set[str]
    date_created: datetime
    date_modified: datetime


async def get_meme_info(meme_key: str) -> MemeInfo:
    return type_validate_python(
        MemeInfo, await send_request(f"/memes/{meme_key}/info", "GET", "JSON")
    )


async def generate_meme_preview(meme_key: str) -> bytes:
    return await send_request(f"/memes/{meme_key}/preview", "GET", "BYTES")


async def generate_meme(
    meme_key: str, images: list[bytes], texts: list[str], args: dict[str, Any]
) -> bytes:
    files = [("images", image) for image in images]
    data = {"texts": texts, "args": json.dumps(args)}
    return await send_request(
        f"/memes/{meme_key}/", "POST", "BYTES", files=files, data=data
    )
